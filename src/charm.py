#!/usr/bin/env python3

"""InfluxDBOperator."""

import logging
import urllib.error
import urllib.request
from typing import Union

import ops

from constants import INFLUXDB_PEER, INFLUXDB_PORT
from exceptions import IngressAddressUnavailableError
from influxdb_ops import (
    InfluxDBOps,
    InfluxDBOpsError,
    create_influxdb_admin_user,
    install,
    version,
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
        logger.debug("Creating influxdb admin user/password.")

        admin_password = create_influxdb_admin_user()
        self.app.add_secret(
            {
                "password": admin_password,
            },
            label="influxdb-admin-password",
        )

        try:
            install()
        except InfluxDBOpsError as e:
            logger.error(e)
            self.unit.status = ops.BlockedStatus("Influxdb install failed.")
            event.defer()
            return

        self._stored.influxdb_installed = True
        self._on_update_status(event)

    def _on_start(self, event: ops.StartEvent) -> None:
        """Handle start hook operations."""
        self.unit.open_port("tcp", int(INFLUXDB_PORT))
        self.unit.set_workload_version(version())

    def _on_config_changed(self, event: ops.ConfigChangedEvent) -> None:
        """Perform config-changed hook."""
        pass

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

    def _on_get_admin_password_action(self, event: ops.ActionEvent) -> None:
        """Return the ldap admin password."""
        event.set_results({"password": self.influxdb_admin_password})


if __name__ == "__main__":  # pragma: nocover
    ops.main(InfluxDBOperator)
