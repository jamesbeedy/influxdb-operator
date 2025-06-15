"""InfluxdbClient."""

import logging

import ops

logger = logging.getLogger()


class InfluxDBClient(ops.Object):
    """InfluxDBClient interface."""

    def __init__(self, charm, relation_name):
        """Set self._relation_name and self.charm."""
        super().__init__(charm, relation_name)
        self._charm = charm
        self._relation_name = relation_name

        self.framework.observe(
            self._charm.on[self._relation_name].relation_changed,
            self._on_relation_changed,
        )

    def _on_relation_changed(self, event: ops.RelationChangedEvent) -> None:
        """Get the data on relation changed."""
        if event_app_data := event.relation.data.get(event.app):
            if secret_id := event_app_data.get("influx_client_creds_secret_id"):
                self._charm.secret_id = secret_id
