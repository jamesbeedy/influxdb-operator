#!/usr/bin/env python3

"""InfluxDBClient."""

import logging

import ops

from interface_influxdb_client import InfluxDBClient

logger = logging.getLogger(__name__)


class InfluxDBClientCharm(ops.CharmBase):
    """InfluxDBClient lifecycle events."""

    _stored = ops.StoredState()

    def __init__(self, *args, **kwargs):
        """Init _stored attributes and interfaces, observe events."""
        super().__init__(*args, **kwargs)

        self._stored.set_default(secret_id=str(), install_complete=False)

        self._influxdb_client = InfluxDBClient(self, "influxdb")

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.get_influxdb_creds_action: self._on_get_influxdb_creds_action,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    @property
    def influxdb_creds(self) -> dict:
        """Return the influxdb-client creds."""
        secret_content = {}
        if secret_id := self._stored.secret_id:
            secret = self.model.get_secret(id=secret_id)
            secret_content = secret.get_content(refresh=True)
        return secret_content

    @property
    def secret_id(self) -> str:
        """Set the secret id."""
        return self._stored.secret_id

    @secret_id.setter
    def secret_id(self, secret_id: str) -> None:
        """Return the secret_id."""
        self._stored.secret_id = secret_id

    @property
    def install_complete(self) -> bool:
        """Return t/f from stored state."""
        return self._stored.install_complete

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Perform installation operations for system level dependencies."""
        self._stored.install_complete = True
        self.unit.status = ops.ActiveStatus()

    def _on_get_influxdb_creds_action(self, event: ops.ActionEvent) -> None:
        """Return the influxdb credentials."""
        if (influxdb_creds := self.influxdb_creds) != {}:
            event.set_results(influxdb_creds)
        else:
            event.set_results({"error": "No credentials found"})


if __name__ == "__main__":  # pragma: nocover
    ops.main(InfluxDBClientCharm)
