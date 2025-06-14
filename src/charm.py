#!/usr/bin/env python3

"""InfluxDBOperator."""

import logging
from typing import Any, Dict, Union

import ops
import influx_ops


logger = logging.getLogger(__name__)


class InfluxDBOperator(ops.CharmBase):
    """InfluxDBOperator lifecycle events."""

    def __init__(self, *args, **kwargs):
        """Init _stored attributes and interfaces, observe events."""
        super().__init__(*args, **kwargs)

        event_handler_bindings = {
            self.on.install: self._on_install,
            self.on.start: self._on_start,
            self.on.config_changed: self._on_config_changed,
            self.on.update_status: self._on_update_status,
        }
        for event, handler in event_handler_bindings.items():
            self.framework.observe(event, handler)

    def _on_install(self, event: ops.InstallEvent) -> None:
        """Perform installation operations for system level dependencies."""

        self.unit.status = ops.WaitingStatus("Installing base system dependencies.")
        logger.debug("Installing base dependencies.....")
        try:
            influx_ops.install()
        except influx_ops.InfluxOpsError as e:
            logger.error(e)
            self.unit.status = ops.BlockedStatus("Influxdb install failed.")
            event.defer()
            return

        self._on_update_status(event)

    def _on_start(self, event: ops.StartEvent) -> None:
        """Handle start hook operations."""
        self.unit.set_workload_version(influx_ops.version())

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
        self.unit.status = ActiveStatus()


if __name__ == "__main__":  # pragma: nocover
    main.main(InfluxDBOperator)
