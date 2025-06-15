"""influxdb-apiinterface."""

import logging
import uuid

import ops

from constants import DEFAULT_INFLUXDB_RETENTION_POLICY, INFLUXDB_PORT

_logger = logging.getLogger()


class InfluxDB(ops.Object):
    """InfluxDB API interface."""

    def __init__(self, charm, relation_name):
        """Set self._relation_name and self.charm."""
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name

        self.framework.observe(
            self._charm.on[self._relation_name].relation_joined,
            self._on_relation_joined,
        )

        self.framework.observe(
            self._charm.on[self._relation_name].relation_broken,
            self._on_relation_broken,
        )

    def _on_relation_joined(self, event: ops.RelationJoinedEvent) -> None:
        """Create a database and user/password for influxdb."""
        if not self.model.unit.is_leader():
            return

        if not self._charm.influxdb_installed:
            event.defer()
            return

        database_name = f"{uuid.uuid4()}"
        if user_pass := self._charm.influxdb_ops.create_user_and_database(database_name):
            secret = self.model.app.add_secret(
                {
                    **user_pass,
                    "host": self._charm.ingress_address,
                    "port": INFLUXDB_PORT,
                    "database": database_name,
                    "policy": DEFAULT_INFLUXDB_RETENTION_POLICY,
                },
                label=f"{event.app.name}-influxdb-credentials",
            )
            secret.grant(event.relation)

            secret_id = secret.id if secret.id is not None else ""
            event.relation.data[self.model.app]["influx_client_creds_secret_id"] = secret_id
            return

        event.defer()

    def _on_relation_broken(self, event: ops.RelationBrokenEvent) -> None:
        """Clear the influxdb info if the relation is broken."""
        if self.model.unit.is_leader():
            event.relation.data[self.model.app]["influxdb_info"] = ""
