from homeassistant import core, config_entries
from .const import DOMAIN, CONF_VERSION, CONF_WALLET, CONF_WALLETS, CONF_WALLET_COUNT, CONF_INTEGRATION, CONF_INTEGRATION_VALUES
import logging
import asyncio

_LOGGER = logging.getLogger(__name__)


# Example migration function
async def async_migrate_entry(hass: core.HomeAssistant, config_entry: config_entries.ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:

        new = {**config_entry.data}
        # TODO: modify Config Entry data
        new[CONF_INTEGRATION] = 'wallet'
        new[CONF_WALLET] = new[CONF_WALLETS][0]
        new[CONF_VERSION] = 2
        del new[CONF_WALLETS]
        del new[CONF_WALLET_COUNT]

        config_entry.version = 2
        config_entry.title = 'Wallet (Migrated) '+new[CONF_WALLET][0:4]
        hass.config_entries.async_update_entry(config_entry, data=new)

    _LOGGER.info("Migration to version %s successful", config_entry.version)

    return True

async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the GitHub Custom component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(
    hass: core.HomeAssistant, 
    entry: config_entries.ConfigEntry
) -> bool:
    """Set up the Helium Integration component."""
    
    #return True
    #print(entry)
    hass.data.setdefault(DOMAIN, {})
    hass_data = dict(entry.data)
    hass.data[DOMAIN][entry.entry_id] = hass_data
    #_LOGGER.exception(entry)
    # Forward the setup to the sensor platform.
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

async def async_unload_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]
        )
    )
    
    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok