import voluptuous as vol
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from .ledvance_device import LedvanceOrbisDevice

DATA_SCHEMA = vol.Schema({
    vol.Required("device_id"): str,
    vol.Required("ip"): str,
    vol.Required("local_key"): str
})

class LedvanceOrbisConfigFlow(config_entries.ConfigFlow, domain="ledvance_orbis"):
    async def async_step_user(self, user_input=None):
        if user_input is not None:
            device = LedvanceOrbisDevice(
                user_input["device_id"],
                user_input["ip"],
                user_input["local_key"]
            )
            # Cihaz doğrulamasını burada yapabiliriz
            if device.get_status():
                return self.async_create_entry(title="Ledvance Orbis Device", data=user_input)
            else:
                return self.async_abort(reason="device_not_found")

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
