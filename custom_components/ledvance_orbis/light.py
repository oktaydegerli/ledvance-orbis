from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    SUPPORT_BRIGHTNESS,
    LightEntity,
)

from homeassistant.components.light import LightEntity
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
        self._brightness = 0
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
    def supported_features(self):
        return SUPPORT_BRIGHTNESS

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on
    
    @property
    def brightness(self):
        return self._brightness

    async def async_turn_on(self, **kwargs):
        """Turn on the light."""
        def turn_on():
            try:
                if ATTR_BRIGHTNESS in kwargs:
                    self._brightness = kwargs[ATTR_BRIGHTNESS]                
                self._device.set_multiple_values({
                    '20': True,
                    '22': int(self._brightness * (1000 / 255))
                })
                return True
            except Exception as e:
                return False

        success = await self.hass.async_add_executor_job(turn_on)
        if success:
            self._is_on = True
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
        def get_status():
            try:
                return self._device.status()
            except Exception:
                return None

        status = await self.hass.async_add_executor_job(get_status)
        if status is not None:
            self._is_on = status.get('dps', {}).get('20', False)
            self._brightness = int(status.get('dps', {}).get('22', 1) / (1000 / 255))