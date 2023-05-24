from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests
from ..const import (
    COINGECKO_PRICE_URL,
    CURRENCY_USD,
    DOMAIN
)
import asyncio


class PriceSensor(Entity):
    """Price Sensor for Solana tokens"""

    def __init__(self, api, address, name = "", symbol = ''):
        super().__init__()
        self.api = api
        self.address = address
        self.symbol = symbol
        self._state = None
        self._available = True
        self._icon = 'mdi:currency-usd'
        self.attributes = {}
        self.device_unique_id = 'helium.price'
        
        if name != '':
            self._unique_id = 'helium.price.'+name.lower()
            self._name = 'Helium Price '+name
            self.node_name = name
        else:
            self._unique_id = 'helium.price.'+address
            self._name = 'Helium Price '+address
            self.node_name = address

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

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device_unique_id)
            },
            name='Helium Price',
            node_name=self.node_name,
            manufacturer='Helium'
        )
    async def async_update(self):
        try:
            response = await asyncio.to_thread(self.api,COINGECKO_PRICE_URL+'?ids='+self.symbol+'&vs_currencies=usd')
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
