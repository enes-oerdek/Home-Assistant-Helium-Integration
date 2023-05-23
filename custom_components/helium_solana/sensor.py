"""Helium Solana Integration"""
import asyncio
import requests
import voluptuous as vol

import logging
import re
from datetime import timedelta
from typing import Any, Callable, Dict, Optional
from urllib import parse

from homeassistant import config_entries, core
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

from .utility import http_client

from .api.heliumstats import HeliumStatsAPI 
from .api.backend import BackendAPI
from .sensors.WalletBalance import WalletBalance
from .sensors.HotspotReward import HotspotReward
from .sensors.HeliumStats import HeliumStats
from .sensors.PriceSensor import PriceSensor

from .const import (
    DOMAIN,
    CONF_WALLET,
    CONF_WALLETS,
    CONF_HOTSPOTS,
    CONF_PRICES,
    HOTSPOTTY_STATS,
    HOTSPOTTY_TOKEN,
    ADDRESS_IOT,
    ADDRESS_MOBILE,
    ADDRESS_HNT,
    ADDRESS_SOLANA
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
api_backend = BackendAPI()

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    wallet = config.get(CONF_WALLET)
    #prices = config.get(CONF_PRICES)
    sensors = await get_sensors([wallet], None)

    async_add_entities(sensors, update_before_add=True)

async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
) -> None:
    """Set up the sensor platform."""
    wallets = config.get(CONF_WALLETS)
    prices = config.get(CONF_PRICES)
    sensors = await get_sensors(wallets, prices)

    async_add_entities(sensors, update_before_add=True)

async def get_sensors(wallets, prices):
    sensors = []
    sensors.append(PriceSensor(http_client, ADDRESS_IOT, 'IOT', 'helium-iot'))
    sensors.append(PriceSensor(http_client, ADDRESS_MOBILE, 'MOBILE', 'helium-mobile'))
    sensors.append(PriceSensor(http_client, ADDRESS_HNT, 'HNT','helium'))
    sensors.append(PriceSensor(http_client, ADDRESS_SOLANA, 'SOLANA', 'wrapped-solana'))


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
        
        sensors.append(WalletBalance(api_backend, wallet, 'hnt', ['balance', 'hnt'], 'HNT','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'iot', ['balance', 'iot'], 'IOT','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'sol', ['balance', 'solana'], 'SOL','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'mobile', ['balance', 'mobile'], 'MOBILE','mdi:wallet'))

        response = await api_backend.get_data('hotspot-rewards2/'+str(wallet))
        if response.status_code == 200:
            rewards = response.json()
            #hotspots = len(rewards.rewards)
            for hotspot_index in rewards['rewards']:
                hotspot_name = rewards['rewards'][hotspot_index]['name']
                hotspot_token = rewards['rewards'][hotspot_index]['token']
                sensors.append(HotspotReward(api_backend, wallet, hotspot_name, ['rewards', hotspot_index, 'claimed_rewards'], 'Claimed Rewards' , hotspot_token, 'mdi:hand-coin-outline'))
                sensors.append(HotspotReward(api_backend, wallet, hotspot_name, ['rewards', hotspot_index, 'unclaimed_rewards'], 'Unclaimed Rewards' , hotspot_token, 'mdi:hand-coin-outline'))
                sensors.append(HotspotReward(api_backend, wallet, hotspot_name, ['rewards', hotspot_index, 'total_rewards'], 'Total Rewards' , hotspot_token, 'mdi:hand-coin-outline'))


            for token in rewards['rewards_aggregated']:
                sensors.append(HotspotReward(api_backend, wallet, wallet, ['rewards_aggregated', token, 'claimed_rewards'], 'Claimed Rewards' , token, 'mdi:hand-coin-outline'))
                sensors.append(HotspotReward(api_backend, wallet, wallet, ['rewards_aggregated', token, 'unclaimed_rewards'], 'Unclaimed Rewards', token, 'mdi:hand-coin-outline'))
                sensors.append(HotspotReward(api_backend, wallet, wallet, ['rewards_aggregated', token, 'total_rewards'], 'Total Rewards', token, 'mdi:hand-coin-outline'))


        #_LOGGER.info(rewards)


    #sensors.append(HotspotReward(backendAPI, wallet, 'iot', ['rewards', ADDRESS_IOT], 'IOT', 'mdi:hand-coin-outline'))
    #sensors.append(HotspotReward(backendAPI, wallet, 'mobile', ['rewards', ADDRESS_MOBILE], 'MOBILE', 'mdi:hand-coin-outline'))

    return sensors