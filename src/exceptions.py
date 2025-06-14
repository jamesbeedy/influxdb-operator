# Copyright (c) 2025 Vantage Compute Corporation
# See LICENSE file for licensing details.

"""Custom exceptions for the influxdb operator."""


class IngressAddressUnavailableError(RuntimeError):
    """Exception raised when getting the ingress-address fails."""

    @property
    def message(self) -> str:
        """Return message passed as argument to exception."""
        return self.args[0]
