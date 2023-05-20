from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests
from ..utility import title_case_and_replace_hyphens


class HotspotReward(Entity):
    """Hotspot Reward"""
    def __init__(self, api, wallet, identifier, path, label, uom, icon):
        super().__init__()
        self.api = api
        self.wallet = wallet
        self.path = path
        self.identifier = identifier
        self._available = True
        self._icon = icon
        self._unique_id = 'helium.hotspot-reward.'+wallet[:4]+'_'+path[0]+"_"+path[1]+"_"+path[2]
        if path[0] == 'rewards_aggregated':
            self._name = 'Helium Wallet '+identifier[:4]+' '+label+" "+uom.upper()
        elif path[0] == 'rewards':
            self._name = 'Helium Hotspot '+title_case_and_replace_hyphens(identifier)+' '+label+" "+uom.upper()

        self.uom = uom.upper()

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
            response = await self.api.get_data('hotspot-rewards2/'+str(self.wallet))
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
