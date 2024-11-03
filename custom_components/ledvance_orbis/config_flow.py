from homeassistant import config_entries
import voluptuous as vol

class LedvanceOrbisConfigFlow(config_entries.ConfigFlow, domain="ledvance_orbis"):
    VERSION = 1
    
    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(
                title="Ledvance Orbis",
                data=user_input
            )

        data_schema = vol.Schema({
            vol.Required("device_id"): str,
            vol.Required("device_ip"): str,
            vol.Required("local_key"): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors
        )
