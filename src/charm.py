#!/usr/bin/env python3

"""InfluxDBOperator."""

import logging
import urllib.error
import urllib.request
from typing import Union

import ops

from constants import INFLUXDB_PEER, INFLUXDB_PORT, INFLUXDB_ADMIN_USERNAME, INFLUXDB_ADMIN_PASSWORD_SECRET_LABEL
from exceptions import IngressAddressUnavailableError
from influxdb_ops import (
    InfluxDBOps,
    InfluxDBOpsError,
    create_influxdb_admin_user,
    write_influxdb_configuration_and_restart_service,
    install as influxdb_install,
    version as influxdb_version,
)
from interface_influxdb import InfluxDB


logger = logging.getLogger(__name__)


class InfluxDBOperator(ops.CharmBase):
    """InfluxDBOperator lifecycle events."""

    _stored = ops.StoredState()

    def __init__(self, *args, **kwargs):
        """Init _stored attributes and interfaces, observe events."""
        super().__init__(*args, **kwargs)

        self._stored.set_default(influx_installed=False)

        self.influxdb_ops = InfluxDBOps(self)
        self._influxdb = InfluxDB(self, "influxdb")

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.start: self._on_start,
            self.on.config_changed: self._on_config_changed,
            self.on.update_status: self._on_update_status,
            self.on.secret_rotate: self._on_secret_rotate,
            # Actions
            self.on.get_user_password_action: self._on_get_user_password_action,
            self.on.update_user_password_action: self._on_update_user_password_action,
            self.on.create_user_action: self._on_create_user_action,
            self.on.create_user_action: self._on_create_user_action,
            self.on.drop_user_action: self._on_drop_user_action,
            self.on.list_users_action: self._on_list_users_action,
            self.on.create_database: self._on_create_database_action,
            self.on.drop_database_action: self._on_drop_database_action,
            self.on.list_databases_action: self._on_list_databases_action,
            self.on.grant_privilege_action: self._on_grant_privilege_action,
            self.on.revoke_privilege_action: self._on_revoke_privilege_action,
            self.on.list_privileges_action: self._on_list_privileges_action,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    @property
    def ingress_address(self) -> str:
        """Return the ingress_address from the peer relation if it exists."""
        if (peer_binding := self.model.get_binding(INFLUXDB_PEER)) is not None:
            ingress_address = f"{peer_binding.network.ingress_address}"
            logger.debug(f"Influxdb ingress_address: {ingress_address}")
            return ingress_address
        raise IngressAddressUnavailableError("Ingress address unavailable")

    @property
    def influxdb_admin_password(self) -> str:
        """Return the influx admin password from secrets storage."""
        secret = self.model.get_secret(label="influxdb-admin-password")
        return secret.get_content(refresh=True)["password"]

    @property
    def influxdb_installed(self) -> bool:
        """Determine if influxdb is installed."""
        return self._stored.influxdb_installed

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Perform installation operations for system level dependencies."""
        self.unit.status = ops.WaitingStatus("Installing base system dependencies.")
       try:
            influxdb_install()
        except InfluxDBOpsError as e:
            logger.error(e)
            self.unit.status = ops.BlockedStatus("Influxdb install failed.")
            event.defer()
            return

        logger.debug("Creating influxdb admin user.")

        admin_password = create_influxdb_admin_user()
        self.app.add_secret(
            {
                "password": admin_password,
            },
            label=INFLUXDB_ADMIN_PASSWORD_SECRET_LABEL,
            rotate=ops.SecretRotate.DAILY,
        )

        write_influxdb_configuration_and_restart_service()

        self._stored.influxdb_installed = True
        self._on_update_status(event)

    def _on_start(self, event: ops.StartEvent) -> None:
        """Handle start hook operations."""
        self.unit.open_port("tcp", int(INFLUXDB_PORT))
        self.unit.set_workload_version(influxdb_version())

    def _on_update_status(
        self,
        event: Union[
            ops.ConfigChangedEvent,
            ops.UpdateStatusEvent,
            ops.InstallEvent,
            ops.StartEvent,
        ],
    ) -> None:
        """Handle update status."""
        status_code = int()
        req = urllib.request.Request(f"http://{self.ingress_address}:{INFLUXDB_PORT}/ping")

        try:
            with urllib.request.urlopen(req) as res:
                status_code = res.getcode()
        except urllib.error.HTTPError:
            status_code = 0

        if status_code == 204:
            self.unit.status = ops.ActiveStatus()
        else:
            self.unit.status = ops.BlockedStatus(
                "InfluxDB is not accepting connections, please debug."
            )

    def _on_secret_rotate(self, event: ops.SecretRotateEvent):
        """Handle secret rotation."""
        if event.secret.label == INFLUXDB_ADMIN_PASSWORD_SECRET_LABEL:
            event.secret.set_content({'password': update_influxdb_admin_user_password()})

    # Actions
    def _on_get_admin_password_action(self, event: ops.ActionEvent) -> None:
        """Return the InfluxDB admin password."""
        event.set_results({"password": self.influxdb_admin_password})

    def _on_get_user_password_action(self, event: ops.ActionEvent) -> None:
        """Return the password for the given user."""
        username = event.params["username"]
        secret = self.model.get_secret(label=f"influxdb-user-{username}")
        event.set_results({"password": secret.get_content(refresh=True)["password"]})

    def _on_update_user_password_action(self, event: ops.ActionEvent) -> None:
        """Update the password for the given user."""
        username = event.params["username"]
        password = event.params["password"]
        secret = self.model.get_secret(label=f"influxdb-user-{username}")
        secret.set_content(
            {"username": username, "password": password}
        )
        self.influxdb_ops.update_user_password(username, password)
        event.set_results({"result": f"Success. Updated password for: {username}"})

    def _on_create_influxdb_user_action(self, event: ActionEvent) -> None:
        """Create an influxdb user."""
        username = event.params["username"]
        user_pass = self.influxdb_ops.create_user(username)
        self.app.add_secret(
            user_pass,
            label=f"influxdb-user-{username}",
        )
        event.set_results({"results": user_pass})

    def _on_drop_influxdb_user_action(self, event: ActionEvent) -> None:
        """Drop an InfluxDB user."""
        username = event.params["username"]
        self.influxdb_ops.drop_user(username)
        event.set_results({"result": f"Success. Dropped user: {username}"})

    def _on_list_influxdb_users_action(self, event: ActionEvent) -> None:
        """List InfluxDB users."""
        users = self.influxdb_ops.list_users()
        event.set_results({"result": users})

    def _on_create_influxdb_database_action(self, event: ActionEvent) -> None:
        """Create an InfluxDB database."""
        database = event.params["database"]
        self.influxdb_ops.create_database(database)
        event.set_results({"result": f"Success. Created database: {database}"})

    def _on_drop_influxdb_database_action(self, event: ActionEvent) -> None:
        """Drop an InfluxDB database."""
        database = event.params["database"]
        self.influxdb_ops.drop_database(database)
        event.set_results({"result": f"Success. Dropped database: {database}"})

    def _on_list_influxdb_databases_action(self, event: ActionEvent) -> None:
        """List InfluxDB databases."""
        databases = self.influxdb_ops.list_databases()
        event.set_results({"result": databases})

    def _on_grant_prilivege_action(self, event: ActionEvent) -> None:
        """Grant a user permissions on a database."""
        username = event.params["username"]
        database = event.params["database"]
        permission = event.params["permission"]

        self.influxdb_ops.grant_prilivege(username, database, permission)
        event.set_results({"result": f"Success. Granted {username} '{permission}' on {database}"})

    def _on_revoke_prilivege_action(self, event: ActionEvent) -> None:
        """Revoke a user permissions on a database."""
        username = event.params["username"]
        database = event.params["database"]
        permission = event.params["permission"]

        self.influxdb_ops.revoke_prilivege(username, database, permission)
        event.set_results({"result": f"Success. Revoked {username} '{permission}' on {database}"})

    def _on_list_priliveges_action(self, event: ActionEvent) -> None:
        """Revoke a user permissions on a database."""
        username = event.params["username"]
        privileges = self.influxdb_ops.list_priliveges(username)
        event.set_results({"result": priliveges})


if __name__ == "__main__":  # pragma: nocover
    ops.main(InfluxDBOperator)
