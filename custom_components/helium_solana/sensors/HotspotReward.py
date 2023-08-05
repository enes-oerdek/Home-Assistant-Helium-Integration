from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests
from ..utility import title_case_and_replace_hyphens
from ..const import (
    DOMAIN
)

import logging
_LOGGER = logging.getLogger(__name__)

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
        self.uom = uom.upper()

        if path[0] == 'rewards_aggregated':
            self._name = 'Helium Hotspot Reward Wallet '+identifier[:4]+' '+label
            self.device_unique_id = "helium.wallet.rewards."+identifier[:4]
            self.device_name = "Helium Hotspot Reward Wallet "+identifier[:4]
        elif path[0] == 'rewards':
            title = title_case_and_replace_hyphens(identifier)
            self._name = 'Helium Hotspot '+title+' '+label
            self.device_unique_id = "helium.hotspot.rewards."+identifier
            self.device_name = "Helium Hotspot "+title
        
        self.node_name = label


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
                (DOMAIN, self.device_unique_id)
            },
            name=self.device_name,
            node_name=self.node_name,
            manufacturer='Helium'
        )

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
