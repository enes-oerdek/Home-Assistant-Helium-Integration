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

from .api.backend import BackendAPI
from .sensors.WalletBalance import WalletBalance
from .sensors.HotspotReward import HotspotReward
from .sensors.HeliumStats import HeliumStats
from .sensors.PriceSensor import PriceSensor
from .sensors.StakingRewardsPosition import StakingRewardsPosition
from .sensors.StakingRewardsToken import StakingRewardsToken


from .const import (
    DOMAIN,
    CONF_VERSION,
    CONF_INTEGRATION,
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

api_backend = BackendAPI()

async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    integration = config.get(CONF_INTEGRATION)
    wallet = config.get(CONF_WALLET)
    sensors = await get_sensors(integration, wallet, None)
    
    #version = config.get(CONF_VERSION)
    #if version == 2:
    #    integration = config.get(CONF_INTEGRATION)
    #    wallet = config.get(CONF_WALLET)
    #    sensors = await get_sensors(integration, wallet, None)
    #elif version is None:
    #    wallets = config.get(CONF_WALLETS)
        #print(wallets)
    #    sensors = await get_sensors_legacy(wallets, None)
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
    sensors = await get_sensors_legacy(wallets, prices)

    async_add_entities(sensors, update_before_add=True)

async def get_sensors(integration, wallet, prices):
    sensors = []

    if integration == 'general_token_price':
        sensors.append(PriceSensor(http_client, ADDRESS_IOT, 'IOT', 'helium-iot'))
        sensors.append(PriceSensor(http_client, ADDRESS_MOBILE, 'MOBILE', 'helium-mobile'))
        sensors.append(PriceSensor(http_client, ADDRESS_HNT, 'HNT','helium'))
        sensors.append(PriceSensor(http_client, ADDRESS_SOLANA, 'SOLANA', 'wrapped-solana'))

        if prices:
            for price in prices:
                sensors.append(PriceSensor(price))

    if integration == 'general_stats':
        sensors.append(HeliumStats(api_backend, 'IOT', 'total_hotspots', 'Total Hotspots', ['stats', 'iot', 'total_hotspots'], 'mdi:router-wireless', 'Hotspots'))
        sensors.append(HeliumStats(api_backend, 'IOT', 'active_hotspots', 'Active Hotspots',  ['stats', 'iot', 'active_hotspots'], 'mdi:router-wireless', 'Hotspots'))
        sensors.append(HeliumStats(api_backend, 'IOT', 'total_cities', 'Total Cities', ['stats', 'iot', 'total_cities'],'mdi:city', 'Cities'))
        sensors.append(HeliumStats(api_backend, 'IOT', 'total_countries', 'Total Countries', ['stats', 'iot', 'total_countries'], 'mdi:earth', 'Countries'))
        sensors.append(HeliumStats(api_backend, 'IOT', 'daily_average_rewards', 'Daily Average Rewards', ['stats', 'iot', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'IOT', 'float'))

        sensors.append(HeliumStats(api_backend, 'MOBILE', 'total_hotspots', 'Total Hotspots', ['stats', 'mobile', 'total_hotspots'],'mdi:router-wireless', 'Hotspots'))
        sensors.append(HeliumStats(api_backend, 'MOBILE', 'active_hotspots', 'Active Hotspots', ['stats', 'mobile', 'active_hotspots'],'mdi:router-wireless', 'Hotspots'))
        sensors.append(HeliumStats(api_backend, 'MOBILE', 'total_cities', 'Total Cities', ['stats', 'mobile', 'total_cities'], 'mdi:city', 'Cities'))
        sensors.append(HeliumStats(api_backend, 'MOBILE', 'total_countries', 'Total Countries', ['stats', 'mobile', 'total_countries'], 'mdi:earth', 'Countries'))
        sensors.append(HeliumStats(api_backend, 'MOBILE', 'daily_average_rewards', 'Daily Average Rewards', ['stats', 'mobile', 'daily_average_rewards'], 'mdi:hand-coin-outline', 'MOBILE' ,'float'))

    if integration == 'wallet':
        
    #if integration == 'wallet_balance':
        sensors.append(WalletBalance(api_backend, wallet, 'hnt', ['balance', 'hnt'], 'HNT','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'iot', ['balance', 'iot'], 'IOT','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'sol', ['balance', 'solana'], 'SOL','mdi:wallet'))
        sensors.append(WalletBalance(api_backend, wallet, 'mobile', ['balance', 'mobile'], 'MOBILE','mdi:wallet'))
    #if integration == 'wallet_hotspots':
        response = None
        try:
            response = await api_backend.get_data('hotspot-rewards2/'+str(wallet))
        except:
            _LOGGER.exception("No hotspot rewards found")
        
        if response and response.status_code == 200:
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


    #if integration == 'wallet_staking':
        response = None
        try:
            response = await api_backend.get_data('staking-rewards/'+str(wallet))
        except:
            _LOGGER.exception("No staking rewards found")
        
        if response.status_code == 200:
            rewards = response.json()
            for delegated_position_key in rewards['rewards']:
                sensors.append(StakingRewardsPosition(api_backend, wallet, delegated_position_key, rewards['rewards'][delegated_position_key], 'mdi:hand-coin-outline'))
                #pass
            
            for token in rewards['rewards_aggregated']:
                sensors.append(StakingRewardsToken(api_backend, wallet, token, 'mdi:hand-coin-outline'))
                #pass

    return sensors

async def get_sensors_legacy(wallets, prices):
    sensors = []
    sensors += await get_sensors('general_token_price', None, prices)
    sensors += await get_sensors('general_stats', None, None)


    for wallet in wallets:
        len_wallet = len(wallet)
        if len_wallet <32 or len_wallet > 44:
            continue
        
        sensors += await get_sensors('wallet', wallet, None)
        #sensors += await get_sensors('wallet_balance', wallet, None)
        #sensors += await get_sensors('wallet_hotspots', wallet, None)
        #sensors += await get_sensors('wallet_staking', wallet, None)

    return sensors