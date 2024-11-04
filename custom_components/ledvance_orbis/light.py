from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP,
    SUPPORT_COLOR,
    LightEntity,
)

from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.color as color_util
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

def map_range(value, from_lower, from_upper, to_lower, to_upper):
    mapped = (value - from_lower) * (to_upper - to_lower) / (from_upper - from_lower) + to_lower
    return round(min(max(mapped, to_lower), to_upper))

class LedvanceOrbis(LightEntity):
    def __init__(self, hass, device_id, device_ip, local_key):
        self.hass = hass
        self._device_id = device_id
        self._device_ip = device_ip
        self._local_key = local_key
        
        self._is_on = False
        self._brightness = 1000
        self._color_temp = 1000
        self._hs = None

        self._lower_brightness = 29
        self._upper_brightness = 1000
        self._upper_color_temp = 1000
        self._max_mired = color_util.color_temperature_kelvin_to_mired(2700)
        self._min_mired = color_util.color_temperature_kelvin_to_mired(6500)

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
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR

    @property
    def is_on(self):
        return self._is_on

    @property
    def brightness(self):
        return map_range(self._brightness, self._lower_brightness, self._upper_brightness, 0, 255)
    
    @property
    def color_temp(self):
        return int(self._max_mired - (((self._max_mired - self._min_mired) / self._upper_color_temp) * self._color_temp))

    @property
    def min_mireds(self):
        return self._min_mired

    @property
    def max_mireds(self):
        return self._max_mired
    
    @property
    def hs_color(self):
        return self._hs
    
    # def __is_color_rgb_encoded(self):
    #    return len(self.dps_conf(24)) > 12

    async def async_turn_on(self, **kwargs):
        def turn_on():
            try:
                self._is_on = True
                if ATTR_BRIGHTNESS in kwargs:
                    self._brightness = map_range(int(kwargs[ATTR_BRIGHTNESS]), 0, 255, self._lower_brightness, self._upper_brightness)
                if ATTR_COLOR_TEMP in kwargs:
                    mired = int(kwargs[ATTR_COLOR_TEMP])
                    if mired < self._min_mired:
                        mired = self._min_mired
                    elif mired > self._max_mired:
                        mired = self._max_mired
                    self._color_temp = int(self._upper_color_temp - (self._upper_color_temp / (self._max_mired - self._min_mired)) * (mired - self._min_mired))
                if ATTR_HS_COLOR in kwargs:
                    self._hs = kwargs[ATTR_HS_COLOR]
                    color = "{:04x}{:04x}{:04x}".format(round(self._hs[0]), round(self._hs[1] * 10.0), self._brightness)
                    #if self.__is_color_rgb_encoded():
                    #    rgb = color_util.color_hsv_to_RGB(self._hs[0], self._hs[1], int(self._brightness * 100 / self._upper_brightness))
                    #    color = "{:02x}{:02x}{:02x}{:04x}{:02x}{:02x}".format(round(rgb[0]), round(rgb[1]), round(rgb[2]), round(self._hs[0]), round(self._hs[1] * 255 / 100), self._brightness)
                    #else:
                    #    color = "{:04x}{:04x}{:04x}".format(round(self._hs[0]), round(self._hs[1] * 10.0), self._brightness)

                self._device.set_multiple_values({
                    '20': self._is_on,
                    '22': self._brightness,
                    '23': self._color_temp,
                    '24': color
                })
                return True
            except Exception as e:
                return False
            
        success = await self.hass.async_add_executor_job(turn_on)
        if success:
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        def turn_off():
            try:
                self._is_on = False
                self._device.set_multiple_values({
                    '20': self._is_on
                })
                return True
            except Exception as e:
                return False

        success = await self.hass.async_add_executor_job(turn_off)
        if success:
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