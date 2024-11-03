from homeassistant import config_entries
from homeassistant.const import CONF_DEVICE_ID, CONF_IP_ADDRESS, CONF_LOCAL_KEY
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN

class LedvanceOrbisConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_DEVICE_ID): str,
                        vol.Required(CONF_IP_ADDRESS): str,
                        vol.Required(CONF_LOCAL_KEY): str,
                    }
                ),
            )

        return self.async_create_entry(
            title=user_input[CONF_DEVICE_ID],
            data=user_input,
        )