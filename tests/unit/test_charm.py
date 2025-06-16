#!/usr/bin/env python3
# Copyright 2025 (c) Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Unit tests for the InfluxDB operator."""

from unittest import TestCase
from unittest.mock import Mock, PropertyMock, patch

from charm import InfluxDBOperator
from influxdb_ops import InfluxDBOpsError

from ops.model import ActiveStatus, BlockedStatus
from scenario import Context, State


class TestCharm(TestCase):
    """Unit test influxdb charm."""

    def setUp(self) -> None:
        """Set up unit test."""
        self.ctx = Context(InfluxDBOperator)

    @patch("influxdb_ops.apt.update")
    @patch("influxdb_ops.apt.add_package")
    @patch("ops.framework.EventBase.defer")
    def test_install_success(self, defer, *_) -> None:
        """Test install success behavior."""
        with self.ctx(self.ctx.on.install(), State()) as manager:
            manager.charm.influxdb_ops.install = Mock()
            manager.charm.influxdb_ops.write_influxdb_configuration_and_restart_service = Mock()
            manager.charm.influxdb_ops.version = Mock(return_value="24.05.2-1")
            manager.run()
            self.assertEqual(
                manager.charm.unit.status,
                ActiveStatus(),
            )
            self.assertTrue(manager.charm._stored.influxdb_installed)

        defer.assert_not_called()

    @patch("ops.framework.EventBase.defer")
    def test_install_fail(self, defer, *_) -> None:
        """Test install failure behavior."""
        with self.ctx(self.ctx.on.install(), State()) as manager:
            manager.charm.influxdb_ops.install = Mock(
                side_effect=InfluxDBOpsError("Failed to install InfluxDB.")
            )
            manager.run()
            self.assertEqual(
                manager.charm.unit.status,
                BlockedStatus("Influxdb install failed."),
            )
            self.assertFalse(manager.charm._stored.influxdb_installed)
        defer.assert_called()
