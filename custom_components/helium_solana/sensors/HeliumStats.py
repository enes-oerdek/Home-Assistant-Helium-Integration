from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests
from ..const import (
    DOMAIN
)


class HeliumStats(Entity):
    """Helium Stats"""
    def __init__(self, api, token, key, name, path, icon, uom, type='int'):
        super().__init__()
        self.api = api
        self.token = token
        self.key = key
        self.path = path
        self._available = True
        self._icon = icon
        self._unique_id = 'helium.stats.'+token+'_'+key.lower()
        self.device_unique_id = 'helium.stats.'+token
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
                (DOMAIN, self.device_unique_id)
            },
            name='Helium Stats '+self.token,
            node_name=self.name,
            manufacturer='Helium'
        )

    
    async def async_update(self):
        try:

            
            response = await self.api.get_data()

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
