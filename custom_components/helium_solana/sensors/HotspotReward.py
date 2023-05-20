from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests


class HotspotReward(Entity):
    """Hotspot Reward"""
    def __init__(self, api, address, key, path, uom, icon):
        super().__init__()
        self.api = api
        self.address = address
        self.key = key
        self.path = path
        self._available = True
        self._icon = icon
        self._unique_id = 'helium.hotspot-reward.'+address[:4]+'_'+key.lower()
        self._name = 'Hotspot Rewards '+address[:4]+' '+uom+" Balance"
        self.uom = uom

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

    async def async_update(self):
        try:
            response = await self.api.get_data('hotspot-rewards/'+str(self.address))
            if response.status_code != 200:
                return
            
            value = response.json()
            for key in self.path:
                value = value[key]
            value = int(value)
            value = round(value / (10 ** 6),2)
            self._state = value
            self._available = True

        except (requests.exceptions.RequestException):
            self._available = False
            _LOGGER.exception("Error retrieving wallet balance from backend")
