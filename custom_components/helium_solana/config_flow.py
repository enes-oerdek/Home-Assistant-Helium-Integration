from homeassistant import config_entries
from .const import DOMAIN, CONF_WALLET, CONF_WALLET_COUNT, CONF_WALLETS
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

class HeliumSolanaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1

    async def async_step_user(self, info):
        if info is not None:
            
            self.data = {}
            self.data[CONF_WALLET_COUNT] = info[CONF_WALLET_COUNT]
            self.data[CONF_WALLETS] = []

            return self.async_show_form(
                step_id="wallets", data_schema=vol.Schema({vol.Required(CONF_WALLET): str})
            )

        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_WALLET_COUNT, default=1): int})
        )
    
    async def async_step_wallets(self, info):
   
        self.data[CONF_WALLETS].append(info[CONF_WALLET])

        if self.data[CONF_WALLET_COUNT] == len(self.data[CONF_WALLETS]):
            return self.async_create_entry(title="Helium Integration", data=self.data)
        
        return self.async_show_form(
            step_id="wallets", data_schema=vol.Schema({vol.Required(CONF_WALLET): str})
        )
        