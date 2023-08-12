from homeassistant import config_entries
from .const import DOMAIN, CONF_VERSION, CONF_WALLET, CONF_WALLET_COUNT, CONF_WALLETS, CONF_INTEGRATION, CONF_INTEGRATION_VALUES
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

class HeliumSolanaConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Example config flow."""
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 2


 
    async def async_step_user(self, info):
        if info is not None:
            selected_integration_label = info[CONF_INTEGRATION]
            selected_integration = [key for key, value in CONF_INTEGRATION_VALUES.items() if value == selected_integration_label]
            if len(selected_integration) != 1:
                return
            selected_integration = selected_integration[0]
            self.data = {}
            self.data[CONF_VERSION] = self.VERSION
            self.data[CONF_INTEGRATION] = selected_integration
            self.title = selected_integration_label

            if selected_integration == 'wallet':
                return self.async_show_form(
                    step_id="wallet", data_schema=vol.Schema({vol.Required(CONF_WALLET): str})
                )
            
            return self.async_create_entry(title=self.title, data=self.data)
        return self.async_show_form(
            step_id="user", data_schema=vol.Schema({vol.Required(CONF_INTEGRATION): vol.In(CONF_INTEGRATION_VALUES.values())})
        )
    
    async def async_step_wallet(self, info):
   
        self.data[CONF_WALLET] = info[CONF_WALLET]
        self.title = self.title+' '+self.data[CONF_WALLET][0:4]
        return self.async_create_entry(title=self.title, data=self.data)
        