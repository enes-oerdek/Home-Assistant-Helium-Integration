"""Helium Solana Integration"""
import asyncio
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
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)

from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from homeassistant.helpers.device_registry import DeviceEntryType


from .api.heliumstats import HeliumStatsAPI 

from .const import (
    DOMAIN,
    CONF_WALLET,
    CONF_HOTSPOT,
    CONF_PRICES,
    HOTSPOTTY_STATS,
    HOTSPOTTY_PRICES,
    HOTSPOTTY_TOKEN,
    ADDRESS_IOT,
    ADDRESS_MOBILE,
    ADDRESS_HNT,
    ADDRESS_SOLANA,
    COINGECKO_PRICE_URL,
    JUPITER_PRICE_URL,
    CURRENCY_USD
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=10)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_WALLET): [cv.string],
        vol.Optional(CONF_HOTSPOT): [cv.string],
        vol.Optional(CONF_PRICES): [cv.string],
    }
)

heliumStatsAPI = HeliumStatsAPI(HOTSPOTTY_STATS, HOTSPOTTY_TOKEN)


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

    sensors = []
    sensors.append(PriceSensor(ADDRESS_IOT, 'IOT', 'helium-iot'))
    sensors.append(PriceSensor(ADDRESS_MOBILE, 'MOBILE', 'helium-mobile'))
    sensors.append(PriceSensor(ADDRESS_HNT, 'HNT','helium'))
    sensors.append(PriceSensor(ADDRESS_SOLANA, 'SOLANA', 'wrapped-solana'))

    prices = config.get(CONF_PRICES)

    if prices:
        for price in prices:
            sensors.append(PriceSensor(price))

    sensors.append(HeliumStats('IOT', 'total_hotspots', 'Total Hotspots', ['data', 'helium_iot', 'total_hotspots'], 'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats('IOT', 'active_hotspots', 'Active Hotspots',  ['data', 'helium_iot', 'active_hotspots'], 'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats('IOT', 'total_cities', 'Total Cities', ['data', 'helium_iot', 'total_cities'],'mdi:city', 'Cities'))
    sensors.append(HeliumStats('IOT', 'total_countries', 'Total Countries', ['data', 'helium_iot', 'total_countries'], 'mdi:earth', 'Countries'))
    sensors.append(HeliumStats('IOT', 'daily_average_rewards', 'Daily Average Rewards', ['data', 'helium_iot', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'IOT', 'float'))

    sensors.append(HeliumStats('MOBILE', 'total_hotspots', 'Total Hotspots', ['data', 'helium_mobile', 'total_hotspots'],'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats('MOBILE', 'active_hotspots', 'Active Hotspots', ['data', 'helium_mobile', 'active_hotspots'],'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats('MOBILE', 'total_cities', 'Total Cities', ['data', 'helium_mobile', 'total_cities'], 'mdi:city', 'Cities'))
    sensors.append(HeliumStats('MOBILE', 'total_countries', 'Total Countries', ['data', 'helium_mobile', 'total_countries'], 'mdi:earth', 'Countries'))
    sensors.append(HeliumStats('MOBILE', 'daily_average_rewards', 'Daily Average Rewards', ['data', 'helium_mobile', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'MOBILE' ,'float'))

    async_add_entities(sensors, update_before_add=True)

class HeliumStats(Entity):
    """Helium Stats"""
    def __init__(self, token, key, name, path, icon, uom, type='int'):
        super().__init__()
        self.token = token
        self.key = key
        self.path = path
        self._available = True
        self._icon = icon
        self._unique_id = 'helium.stats.'+token+'_'+key.lower()
        self._name = 'Helium Stats '+token+' '+name
        self.uom = uom
        self.type = type

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
        return self._icon
    
    @property
    def should_poll(self):
        return True

    @property
    def unit_of_measurement(self):
        return self.uom

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._unique_id)
            },
            name='Helium Stat '+self.token+' '+self.name,
            node_name='Helium Stat '+self.token+' '+self.name,
            manufacturer='Helium'
        )

    
    async def async_update(self):
        try:

            
            response = await heliumStatsAPI.get_data()

            if response.status_code != 200:
                return
            
            value = response.json()
            for key in self.path:
                value = value[key]

            if self.type == 'str':
                value = str(value)
            elif self.type == 'float':
                value = float(value)
            else:
                value = int(value)
            self._state = value
            self._available = True

        except (requests.exceptions.RequestException):
            self._available = False
            _LOGGER.exception("Error retrieving helium stats from hotspotty")



class PriceSensor(Entity):
    """Price Sensor for Solana tokens"""

    def __init__(self, address, name = "", symbol = ''):
        super().__init__()
        self.address = address
        self.symbol = symbol
        self._state = None
        self._available = True
        self._icon = 'mdi:currency-usd'
        self.attributes = {}
        if name != '':
            self._unique_id = 'helium.price.'+name.lower()
            self._name = 'Helium Price '+name
        else:
            self._unique_id = 'helium.price.'+address
            self._name = 'Helium Price '+address

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
        return self._icon

    @property
    def unit_of_measurement(self):
        return CURRENCY_USD

    @property
    def extra_state_attributes(self):
        return self.attributes

    @property
    def should_poll(self):
        return True

    async def async_update(self):
        try:
            response = await asyncio.to_thread(http_client,COINGECKO_PRICE_URL+'?ids='+self.symbol+'&vs_currencies=usd')
            print(response)
            if response.status_code != 200:
                return
            
            json = response.json()
            price_data = json[self.symbol]
            self._state = float(price_data['usd'])
            #self.attributes['id'] = price_data['id']
            #self.attributes['mintSymbol'] = price_data['mintSymbol']
            #self.attributes['vsToken'] = price_data['vsToken']
            #self.attributes['vsTokenSymbol'] = price_data['vsTokenSymbol']
            self._available = True

        except (requests.exceptions.RequestException):
            self._available = False
            _LOGGER.exception("Error retrieving data from jupiter.")
