"""Helium Solana Integration"""

import requests
import voluptuous as vol

import logging
import re
from datetime import timedelta
from typing import Any, Callable, Dict, Optional
from urllib import parse

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)


from .const import (
    CONF_WALLET,
    CONF_HOTSPOT,
    CONF_PRICES,
    HOTSPOTTY_PRICES,
    ADDRESS_IOT,
    ADDRESS_MOBILE,
    ADDRESS_HNT,
    ADDRESS_SOLANA,
    JUPITER_PRICE_URL
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        #vol.Optional(CONF_WALLET): [cv.string],
        #vol.Optional(CONF_HOTSPOT): [cv.string],
        vol.Optional(CONF_PRICES): [cv.string],
    }
)


def http_client(url, payload=None, method='GET', headers=None):
    # Make the HTTP request with the given URL, payload, method, and headers
    response = requests.request(method, url, json=payload, headers=headers)

    # Raise an exception if the response was not successful
    response.raise_for_status()

    # Return the response
    return response


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    #session = async_get_clientsession(hass)
    #github = GitHubAPI(session, "requester", oauth_token=config[CONF_ACCESS_TOKEN])
    #wallets = config.get(CONF_WALLET)
    #hotspots = config.get(CONF_HOTSPOT)
    prices = config.get(CONF_PRICES)

    prices.append(PriceSensor(ADDRESS_IOT, JUPITER_PRICE_URL, 'IOT'))
    prices.append(PriceSensor(ADDRESS_MOBILE, JUPITER_PRICE_URL, 'MOBILE'))
    prices.append(PriceSensor(ADDRESS_HNT, JUPITER_PRICE_URL, 'HNT'))
    prices.append(PriceSensor(ADDRESS_SOLANA, JUPITER_PRICE_URL, 'SOLANA'))

    for price in prices:
        sensors.append(PriceSensor(price))

    async_add_entities(sensors, update_before_add=True)

class PriceSensor(Entitiy):

    def __init__(self, address, name = ""):
        super().__init__()
        self.address = address
        self._state = None
        self._available = True
        self._icon = 'mdi:currency-usd'
        self.attrs = {}
        if name != '':
            self._unique_id = 'helium.price.'+name.lower()
            self._name = 'Price '+name
        else:
            self._unique_id = 'helium.price.'+address
            self._name = 'Price '+address

    @property
    def name(self) -> str:
        return self._name

    @property
    def unique_id(self) -> str:
        return self._unique_id

    @property
    def available(self) -> bool:
        return self._available

    @property
    def state(self) -> Optional[str]:
        return self._state

    @property
    def icon(self) -> str | None:
        return "mdi:door"

    @property
    def unit_of_measurement(self):
        return CURRENCY_USD

    @property
    def extra_state_attributes(self):
        return self._attrs

    async def async_update(self):
        try:
            response = http_client(JUPITER_PRICE_URL+'?ids='+self.address)
            if response.status_code != 200:
                return
            
            json = response.json()
            self._state = float(json.data[self.address].price)


        except (ClientError):
            self._available = False
            _LOGGER.exception("Error retrieving data from jupyter.")