# Copyright (c) 2025 Vantage Compute Corporation
# See LICENSE file for licensing details.

"""Custom exceptions for the influxdb operator."""


class InfluxDBSecretAccessError(RuntimeError):
    """Exception raised when the charm cannot access s secret id."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]


class IngressAddressUnavailableError(RuntimeError):
    """Exception raised when getting the ingress-address fails."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]
