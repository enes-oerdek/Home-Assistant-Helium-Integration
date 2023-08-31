"""Helium stats entity."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
import logging
from typing import Any, Coroutine

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.device_registry import (
    CONNECTION_BLUETOOTH,
    CONNECTION_NETWORK_MAC,
    format_mac,
)
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.typing import EventType, StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
import requests

from ..api.backend import BackendAPI
from ..const import DOMAIN
from ..coordinator import HeliumSolanaDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


class HeliumStats(CoordinatorEntity[HeliumSolanaDataUpdateCoordinator], SensorEntity):
    """Helium stats sensor entity."""

    _attr_should_poll = True
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: HeliumSolanaDataUpdateCoordinator,
        token: str,
        key: str,
        name: str,
        path: list[str],
        icon: str,
        uom: str | None = None,
        _type: str = "int",
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.token = token
        self.key = key
        self.path = path
        self.device_unique_id = "helium.stats." + token
        self.type = _type

        # self._attr_available = True
        self._attr_device_info = DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device_unique_id)
            },
            name="Helium Stats " + self.token,
            manufacturer="Helium",
        )
        self._attr_icon = icon
        self._attr_name = "Helium Stats " + token + " " + name
        self._attr_native_unit_of_measurement = uom
        self._attr_unique_id = "helium.stats." + token + "_" + key.lower()

        self._set_native_value()

    def _set_native_value(self) -> None:
        if value := self.coordinator.data:
            for key in self.path:
                value = value[key]
            if self.type == "str":
                value = str(value)
            elif self.type == "float":
                value = float(value)
            else:
                value = int(value)
        self._attr_native_value = value

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._set_native_value()
        return super()._handle_coordinator_update()
