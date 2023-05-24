from typing import Any, Callable, Dict, Optional
from homeassistant.helpers.entity import (
    Entity,
    DeviceInfo
)
import requests
from ..const import (
    DOMAIN
)


class WalletBalance(Entity):
    """Wallet Balance"""
    def __init__(self, api, address, key, path, uom, icon):
        super().__init__()
        self.api = api
        self.address = address
        self.key = key
        self.path = path
        self._available = True
        self._icon = icon
        self._unique_id = 'helium.wallet.'+address[:4]+'_'+key.lower()
        self._name = 'Helium Wallet '+address[:4]+' '+uom+" Balance"
        self.uom = uom
        self.device_unique_id = 'helium.wallet.'+address[:4]
        self.node_name = uom

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
            name='Helium Wallet '+self.address[:4],
            node_name=self.node_name,
            manufacturer='Helium'
        )

    async def async_update(self):
        try:
            response = await self.api.get_data('wallet/'+str(self.address))
            if response.status_code != 200:
                return
            
            value = response.json()
            print(value)
            for key in self.path:
                value = value[key]

            value = round(float(value),2)
            self._state = value
            self._available = True

        except (requests.exceptions.RequestException):
            self._available = False
            _LOGGER.exception("Error retrieving wallet balance from backend")
