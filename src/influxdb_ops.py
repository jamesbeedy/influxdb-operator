#!/usr/bin/python3

"""influx_ops."""

import logging
import secrets
import subprocess
from typing import Dict, Optional

import charms.operator_libs_linux.v0.apt as apt
from influxdb import InfluxDBClient

from constants import DEFAULT_INFLUXDB_RETENTION_POLICY, INFLUXDB_ADMIN_USERNAME, INFLUXDB_PORT

_logger = logging.getLogger(__name__)


INFLUX_PACKAGES = ["influxdb", "influxdb-client"]


def create_influxdb_admin_user() -> str:
    """Create the influxdb admin user."""
    client = InfluxDBClient(host="localhost", port=8086)
    admin_password = secrets.token_urlsafe(32)
    try:
        client.create_user(INFLUXDB_ADMIN_USERNAME, admin_password, admin=True)
        _logger.debug("Admin user created successfully.")
    except Exception:
        print("Error creating admin user.")
    finally:
        client.close()
    return admin_password


class InfluxDBOpsError(RuntimeError):
    """Exception raised when a package installation failed."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]


class InfluxDBOps:
    """InfluxDBOps."""

    def __init__(self, charm):
        self._charm = charm

    def _influxdb_admin_client(self) -> InfluxDBClient:
        """Create and return influxdbclient."""
        return InfluxDBClient(
            host="127.0.0.1",
            port=int(INFLUXDB_PORT),
            username=INFLUXDB_ADMIN_USERNAME,
            password=self._charm.influxdb_admin_password,
        )

    def create_user_and_database(self, database_name: str) -> Optional[Dict[str, str]]:
        """Create an influxdb user."""
        client = self._influxdb_admin_client()

        influxdb_username = secrets.token_urlsafe(10)
        influxdb_password = secrets.token_urlsafe(32)

        client.create_user(influxdb_username, influxdb_password)
        client.create_database(database_name)

        client.grant_privilege("all", database_name, influxdb_username)

        client.create_retention_policy(
            name=DEFAULT_INFLUXDB_RETENTION_POLICY,
            duration="7d",
            replication="1",
            database=database_name,
            default=True,
        )

        return {"username": influxdb_username, "password": influxdb_password}


def install() -> None:
    """Install `influxdb`.

    Raises:
        InfluxDBOpsError: Raised if `apt` fails to install `influxdb` on the unit.

    Notes:
        This function uses the `influxdb` packages hosted within the
        upstream InfluxDB PPA located at https://repos.influxdata.com/ubuntu.
    """
    try:
        apt.update()
        _logger.info("installing packages `%s` using apt", INFLUX_PACKAGES)
        apt.add_package(INFLUX_PACKAGES)
        _logger.info("packages `%s` successfully installed on unit", INFLUX_PACKAGES)
    except (apt.PackageNotFoundError, apt.PackageError) as e:
        raise InfluxDBOpsError(
            f"failed to install influxdb packages `{INFLUX_PACKAGES}`. reason: {e}"
        )


def version() -> str:
    """Get the current version of `influxdb` installed on the unit.

    Raises:
        InfluxOpsError: Raised if `influxdb` is not installed on unit.
    """
    try:
        result = subprocess.check_output(["influx", "--version"], text=True)
        return result.split()[-1]
    except (FileNotFoundError, subprocess.CalledProcessError) as e:
        raise InfluxDBOpsError(f"failed to get the version of `influxdb` installed. reason: {e}")
