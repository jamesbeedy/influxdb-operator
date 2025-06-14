#!/usr/bin/python3
import logging
import subprocess

import charms.operator_libs_linux.v0.apt as apt


_logger = logging.getLogger(__name__)

INFLUX_PACKAGES = ["influxdb", "influx-client"]


class InfluxOpsError(RuntimeError):
    """Exception raised when a package installation failed."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]


def install() -> None:
    """Install `influxdb`.

    Raises:
        InfluxOpsError: Raised if `apt` fails to install `influxdb` on the unit.

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
        raise InfluxOpsError(
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
        raise InfluxOpsError(
            f"failed to get the version of `influxdb` installed. reason: {e.stderr}"
        )
