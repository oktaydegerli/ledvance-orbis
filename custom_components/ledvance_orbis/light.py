from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import tinytuya

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device_id = config_entry.data["device_id"]
    device_ip = config_entry.data["device_ip"]
    local_key = config_entry.data["local_key"]
    
    async_add_entities([TuyaLight(device_id, device_ip, local_key)])

class TuyaLight(LightEntity):
    def __init__(self, device_id, device_ip, local_key):
        self._device = tinytuya.BulbDevice(
            dev_id=device_id,
            address=device_ip,
            local_key=local_key,
            version=3.3
        )
        self._is_on = False
        self._name = "Ledvance Orbis"
        self._unique_id = device_id

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._is_on

    def turn_on(self, **kwargs):
        self._device.turn_on()
        self._is_on = True

    def turn_off(self, **kwargs):
        self._device.turn_off()
        self._is_on = False

    def update(self):
        try:
            status = self._device.status()
            if status is not None:
                self._is_on = status.get('dps', {}).get('1', False)
        except Exception:
            pass