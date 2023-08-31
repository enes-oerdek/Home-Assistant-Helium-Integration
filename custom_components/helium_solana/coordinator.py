"""Helium solana data coordinator."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from requests.exceptions import RequestException

from .api.backend import BackendAPI
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=10)


class HeliumSolanaDataUpdateCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, api: BackendAPI) -> None:
        """Initialize."""
        self.api = api
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=UPDATE_INTERVAL)

    async def _async_update_data(self) -> dict | None:
        """Fetch data from API endpoint."""
        try:
            _LOGGER.debug("Requesting data for heliumstats")
            response = await self.api.get_data("heliumstats")
            if response.status_code == 200:
                return response.json()
        except RequestException as ex:
            _LOGGER.exception("Error retrieving helium stats from hotspotty")
            raise UpdateFailed(ex) from ex
