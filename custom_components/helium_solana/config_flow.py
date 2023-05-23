from homeassistant import config_entries
from .const import DOMAIN, CONF_WALLET
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

class HeliumSolanaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, info):
        if info is not None:
            #pass  # TODO: process info
            self.data = info
            return self.async_create_entry(title="Helium Integration", data=self.data)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_WALLET): str})
        )
        