from homeassistant.components.light import LightEntity, ATTR_BRIGHTNESS
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import tinytuya
from functools import partial
import asyncio

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    device_id = config_entry.data["device_id"]
    device_ip = config_entry.data["device_ip"]
    local_key = config_entry.data["local_key"]
    
    light = LedvanceOrbis(hass, device_id, device_ip, local_key)
    await light.async_init()
    async_add_entities([light])

class LedvanceOrbis(LightEntity):
    def __init__(self, hass, device_id, device_ip, local_key):
        self.hass = hass
        self._device_id = device_id
        self._device_ip = device_ip
        self._local_key = local_key
        self._is_on = False
        self._brightness = 255
        self._name = "Ledvance Orbis"
        self._unique_id = f"ledvance_orbis_{device_id}"
        self._device = None

    async def async_init(self):
        """Initialize the device asynchronously."""
        def init_device():
            device = tinytuya.BulbDevice(
                dev_id=self._device_id,
                address=self._device_ip,
                local_key=self._local_key,
                version=3.3
            )
            return device

        self._device = await self.hass.async_add_executor_job(init_device)

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def unique_id(self):
        """Return the unique ID of this light."""
        return self._unique_id

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on
    
    @property
    def brightness(self):
        """Return the brightness of the light."""
        return self._brightness

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_BRIGHTNESS

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        def turn_on():
            try:
                values = {'20': True}
                if ATTR_BRIGHTNESS in kwargs:
                    brightness = kwargs[ATTR_BRIGHTNESS]
                    tuya_brightness = int((brightness / 255) * 1000)
                    values['22'] = tuya_brightness
                self._device.set_multiple_values(values)
                return True
            except Exception as e:
                return False

        success = await self.hass.async_add_executor_job(turn_on)
        if success:
            self._is_on = True
            if ATTR_BRIGHTNESS in kwargs:
                self._brightness = kwargs[ATTR_BRIGHTNESS]
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        """Turn off the light."""
        def turn_off():
            try:
                self._device.set_multiple_values({
                    '20': False
                })
                return True
            except Exception as e:
                return False

        success = await self.hass.async_add_executor_job(turn_off)
        if success:
            self._is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        """Fetch new state data for this light."""
        def get