#!/usr/bin/python3

"""influx_ops."""

import logging
import secrets
import subprocess
from shutil import copy2
from typing import Any, Dict

import charms.operator_libs_linux.v0.apt as apt
from influxdb import InfluxDBClient

from constants import DEFAULT_INFLUXDB_RETENTION_POLICY, INFLUXDB_ADMIN_USERNAME, INFLUXDB_PORT

_logger = logging.getLogger(__name__)


INFLUX_PACKAGES = ["influxdb", "influxdb-client"]


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


def write_influxdb_configuration_and_restart_service() -> None:
    """Write InfluxDB config and restart the service."""
    copy2("./src/templates/influxdb.conf", "/etc/influxdb/influxdb.conf")
    subprocess.run(["systemctl", "restart", "influxdb"])


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


def version() -> str:
    """Test influxdb health by using the ping command to return the version."""
    client = InfluxDBClient(host="localhost", port=8086)
    vers = ""
    try:
        vers = client.ping()
        _logger.debug(f"InfluxDB healthy. Running version: {version}.")
    except Exception:
        print("Error creating admin user.")
    finally:
        client.close()
    return vers


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

    def create_user(self, influxdb_username: str) -> Dict[str, str]:
        """Create an influxdb user."""
        client = self._influxdb_admin_client()

        influxdb_password = secrets.token_urlsafe(32)

        try:
            client.create_user(influxdb_username, influxdb_password)
        except Exception:
            msg = "Error creating user."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("User creation succeeded.")
        return {"username": influxdb_username, "password": influxdb_password}

    def drop_user(self, influxdb_username: str) -> None:
        """Drop an influxdb user."""
        client = self._influxdb_admin_client()

        try:
            client.drop_user(influxdb_username)
        except Exception:
            msg = "Error dropping user."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("User dropped succeeded.")

    def list_users(self) -> list:
        """List influxdb users."""
        client = self._influxdb_admin_client()

        users = []
        try:
            users = client.get_list_users()
        except Exception:
            msg = "Error listing users."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("Listing users succeeded.")
        return users

    def create_database(self, influxdb_database: str) -> None:
        """Create an influxdb database and retention policy."""
        # Database
        client = self._influxdb_admin_client()
        try:
            client.create_database(influxdb_database)
        except Exception:
            msg = "Error creating database."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        # Retention policy
        client = self._influxdb_admin_client()
        try:
            client.create_retention_policy(
                name=DEFAULT_INFLUXDB_RETENTION_POLICY,
                duration="7d",
                replication="1",
                database=influxdb_database,
                default=True,
            )
        except Exception:
            msg = "Error creating default retention policy."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("Database creation succeeded.")

    def drop_database(self, influxdb_database: str) -> None:
        """Drop an influxdb user."""
        client = self._influxdb_admin_client()

        try:
            client.drop_database(influxdb_database)
        except Exception:
            msg = "Error dropping database."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("Database dropped succeeded.")

    def list_databases(self) -> list:
        """List influxdb databases."""
        client = self._influxdb_admin_client()

        databases = []
        try:
            databases = client.get_list_database()
        except Exception:
            msg = "Error listing databases."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("Listing users succeeded.")
        return databases

    def grant_privilege(
        self, influxdb_username: str, influxdb_database: str, privilege: str = "all"
    ) -> None:
        """Grant an influxdb user permissions on a database."""
        client = self._influxdb_admin_client()

        try:
            client.grant_privilege(privilege, influxdb_database, influxdb_username)
        except Exception:
            msg = f"Error granting {privilege} to {influxdb_username} on {influxdb_database}."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug(
            f"Successfully granted {privilege} to {influxdb_username} on {influxdb_database}."
        )

    def revoke_privilege(
        self, influxdb_username: str, influxdb_database: str, privilege: str = "all"
    ) -> None:
        """Revoke an influxdb user privilege on a database."""
        client = self._influxdb_admin_client()

        try:
            client.revoke_privilege(privilege, influxdb_database, influxdb_username)
        except Exception:
            msg = f"Error revoking {privilege} from {influxdb_username} on {influxdb_database}."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug(
            f"Successfully revoked {privilege} to {influxdb_username} on {influxdb_database}."
        )

    def list_privileges(self, influxdb_username: str) -> list:
        """List influxdb databases."""
        client = self._influxdb_admin_client()

        privileges = []
        try:
            privileges = client.get_list_privileges(influxdb_username)
        except Exception:
            msg = "Error listing privileges."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()

        _logger.debug("Listing privileges succeeded.")
        return privileges

    def create_user_and_database(self, influxdb_database: str) -> Dict[Any, Any]:
        """Create an influxdb user."""
        client = self._influxdb_admin_client()

        influxdb_username = secrets.token_urlsafe(10)

        user_pass = {}
        try:
            user_pass = self.create_user(influxdb_username)
            self.create_database(influxdb_database)
            self.grant_privilege(influxdb_username, influxdb_database)
            _logger.debug("Create user password updated successfully.")
        except Exception:
            msg = "Error creating user and database."
            _logger.error(msg)
            InfluxDBOpsError(msg)
        finally:
            client.close()

        return user_pass

    def update_user_password(self, influxdb_username: str, influxdb_password: str) -> None:
        """Create the influxdb admin user."""
        client = self._influxdb_admin_client()
        try:
            client.set_user_password(influxdb_username, influxdb_password)
            _logger.debug("User password updated successfully.")
        except Exception:
            msg = "Error updating user password."
            _logger.error(msg)
            raise InfluxDBOpsError(msg)
        finally:
            client.close()
        _logger.debug("Updating user password succeeded.")

    def update_influxdb_admin_user_password(self) -> str:
        """Update the admin password."""
        password = secrets.token_urlsafe(32)
        self.update_user_password(INFLUXDB_ADMIN_USERNAME, password)
        return password
