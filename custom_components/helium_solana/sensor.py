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
from .api.backend import BackendAPI
from .sensors.WalletBalance import WalletBalance
from .sensors.HotspotReward import HotspotReward
from .sensors.HeliumStats import HeliumStats
from .sensors.PriceSensor import PriceSensor

from .const import (
    DOMAIN,
    CONF_WALLETS,
    CONF_HOTSPOTS,
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
        vol.Optional(CONF_WALLETS): [cv.string],
        vol.Optional(CONF_HOTSPOTS): [cv.string],
        vol.Optional(CONF_PRICES): [cv.string],
    }
)

heliumStatsAPI = HeliumStatsAPI(HOTSPOTTY_STATS, HOTSPOTTY_TOKEN)
api_wallet = BackendAPI()
api_rewards = BackendAPI()

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
    wallets = config.get(CONF_WALLETS)

    sensors = []
    sensors.append(PriceSensor(http_client, ADDRESS_IOT, 'IOT', 'helium-iot'))
    sensors.append(PriceSensor(http_client, ADDRESS_MOBILE, 'MOBILE', 'helium-mobile'))
    sensors.append(PriceSensor(http_client, ADDRESS_HNT, 'HNT','helium'))
    sensors.append(PriceSensor(http_client, ADDRESS_SOLANA, 'SOLANA', 'wrapped-solana'))

    prices = config.get(CONF_PRICES)

    if prices:
        for price in prices:
            sensors.append(PriceSensor(price))

    sensors.append(HeliumStats(heliumStatsAPI, 'IOT', 'total_hotspots', 'Total Hotspots', ['data', 'helium_iot', 'total_hotspots'], 'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats(heliumStatsAPI, 'IOT', 'active_hotspots', 'Active Hotspots',  ['data', 'helium_iot', 'active_hotspots'], 'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats(heliumStatsAPI, 'IOT', 'total_cities', 'Total Cities', ['data', 'helium_iot', 'total_cities'],'mdi:city', 'Cities'))
    sensors.append(HeliumStats(heliumStatsAPI, 'IOT', 'total_countries', 'Total Countries', ['data', 'helium_iot', 'total_countries'], 'mdi:earth', 'Countries'))
    sensors.append(HeliumStats(heliumStatsAPI, 'IOT', 'daily_average_rewards', 'Daily Average Rewards', ['data', 'helium_iot', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'IOT', 'float'))

    sensors.append(HeliumStats(heliumStatsAPI, 'MOBILE', 'total_hotspots', 'Total Hotspots', ['data', 'helium_mobile', 'total_hotspots'],'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats(heliumStatsAPI, 'MOBILE', 'active_hotspots', 'Active Hotspots', ['data', 'helium_mobile', 'active_hotspots'],'mdi:router-wireless', 'Hotspots'))
    sensors.append(HeliumStats(heliumStatsAPI, 'MOBILE', 'total_cities', 'Total Cities', ['data', 'helium_mobile', 'total_cities'], 'mdi:city', 'Cities'))
    sensors.append(HeliumStats(heliumStatsAPI, 'MOBILE', 'total_countries', 'Total Countries', ['data', 'helium_mobile', 'total_countries'], 'mdi:earth', 'Countries'))
    sensors.append(HeliumStats(heliumStatsAPI, 'MOBILE', 'daily_average_rewards', 'Daily Average Rewards', ['data', 'helium_mobile', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'MOBILE' ,'float'))

    for wallet in wallets:
        len_wallet = len(wallet)
        if len_wallet <32 or len_wallet > 44:
            continue
        sensors.append(WalletBalance(api_wallet, wallet, 'hnt', ['balance', 'hnt'], 'HNT','mdi:wallet'))
        sensors.append(WalletBalance(api_wallet, wallet, 'iot', ['balance', 'iot'], 'IOT','mdi:wallet'))
        sensors.append(WalletBalance(api_wallet, wallet, 'sol', ['balance', 'solana'], 'SOL','mdi:wallet'))
        sensors.append(WalletBalance(api_wallet, wallet, 'mobile', ['balance', 'mobile'], 'MOBILE','mdi:wallet'))

        #rewards = await api_rewards.get_data('hotspot-rewards2/'+str(wallet))
        #_LOGGER.info(rewards)


    #sensors.append(HotspotReward(backendAPI, wallet, 'iot', ['rewards', ADDRESS_IOT], 'IOT', 'mdi:hand-coin-outline'))
    #sensors.append(HotspotReward(backendAPI, wallet, 'mobile', ['rewards', ADDRESS_MOBILE], 'MOBILE', 'mdi:hand-coin-outline'))

    async_add_entities(sensors, update_before_add=True)