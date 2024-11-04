from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    ATTR_EFFECT,
    SUPPORT_BRIGHTNESS,
    SUPPORT_COLOR_TEMP,
    SUPPORT_COLOR,
    SUPPORT_EFFECT,
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

MODE_COLOR = "colour"
MODE_MUSIC = "music"
MODE_SCENE = "scene"
MODE_WHITE = "white"

SCENE_CUSTOM = "Custom"
SCENE_MUSIC = "Music"

SCENE_LIST_RGBW_1000 = {
    "Night": "000e0d0000000000000000c80000",
    "Read": "010e0d0000000000000003e801f4",
    "Meeting": "020e0d0000000000000003e803e8",
    "Leasure": "030e0d0000000000000001f401f4",
    "Soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "Rainbow": "05464601000003e803e800000000464601007803e803e80000000046460100f003e803" + "e800000000",
    "Shine": "06464601000003e803e800000000464601007803e803e80000000046460100f003e803e8" + "00000000",
    "Beautiful": "07464602000003e803e800000000464602007803e803e80000000046460200f003e8" + "03e800000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e80" + "3e800000000",
}

SCENE_LIST_RGBW_255 = {
    "Night": "bd76000168ffff",
    "Read": "fffcf70168ffff",
    "Meeting": "cf38000168ffff",
    "Leasure": "3855b40168ffff",
    "Scenario 1": "scene_1",
    "Scenario 2": "scene_2",
    "Scenario 3": "scene_3",
    "Scenario 4": "scene_4",
}

SCENE_LIST_RGB_1000 = {
    "Night": "000e0d00002e03e802cc00000000",
    "Read": "010e0d000084000003e800000000",
    "Working": "020e0d00001403e803e800000000",
    "Leisure": "030e0d0000e80383031c00000000",
    "Soft": "04464602007803e803e800000000464602007803e8000a00000000",
    "Colorful": "05464601000003e803e800000000464601007803e803e80000000046460100f003e80" + "3e800000000464601003d03e803e80000000046460100ae03e803e800000000464601011303e803" + "e800000000",
    "Dazzling": "06464601000003e803e800000000464601007803e803e80000000046460100f003e80" + "3e800000000",
    "Music": "07464602000003e803e800000000464602007803e803e80000000046460200f003e803e8" + "00000000464602003d03e803e80000000046460200ae03e803e800000000464602011303e803e80" + "0000000",
}

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
        self._effect = None
        self._scenes = SCENE_LIST_RGBW_1000
        self._effect_list = list(self._scenes.keys())
        self._effect_list.append(SCENE_MUSIC)

        self._lower_brightness = 29
        self._upper_brightness = 1000
        self._working_mode = MODE_WHITE
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
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR | SUPPORT_EFFECT

    @property
    def is_on(self):
        return self._is_on
    
    @property
    def is_color_mode(self):
        return self._working_mode == MODE_COLOR
    
    @property
    def is_white_mode(self):
        return self._working_mode == MODE_WHITE
    
    @property
    def is_scene_mode(self):
        return self._working_mode == MODE_SCENE
    
    @property
    def is_music_mode(self):
        return self._working_mode == MODE_MUSIC
    
    def __get_color_mode(self):
        if self._working_mode == MODE_COLOR:
            return MODE_COLOR
        else:
            return MODE_WHITE
        
    @property
    def brightness(self):
        if self.is_color_mode or self.is_white_mode:
            return map_range(self._brightness, self._lower_brightness, self._upper_brightness, 0, 255)
        return None

    @property
    def color_temp(self):
        if self.is_white_mode:
            return int(self._max_mired - (((self._max_mired - self._min_mired) / self._upper_color_temp) * self._color_temp))
        else:
            return None

    @property
    def min_mireds(self):
        return self._min_mired

    @property
    def max_mireds(self):
        return self._max_mired
    
    @property
    def hs_color(self):
        if self.is_color_mode:
            return self._hs
        else:
            return None
        
    @property
    def effect(self):
        if self.is_scene_mode or self.is_music_mode:
            return self._effect
        return None
    
    @property
    def effect_list(self):
        return self._effect_list
    
    def __is_color_rgb_encoded(self):
        return False
        #return len(self.dps_conf(24)) > 12

    async def async_turn_on(self, **kwargs):
        def turn_on():
            try:
                self._is_on = True
                brightness = None

                if ATTR_EFFECT in kwargs:
                    scene = self._scenes.get(kwargs[ATTR_EFFECT])
                    if scene is not None:
                        if scene.startswith(MODE_SCENE):
                            self._working_mode = scene
                        else:
                            self._working_mode = MODE_SCENE
                            self._effect = scene
                    elif kwargs[ATTR_EFFECT] == SCENE_MUSIC:
                        self._working_mode = MODE_MUSIC
                
                if ATTR_BRIGHTNESS in kwargs:
                    brightness = map_range(int(kwargs[ATTR_BRIGHTNESS]), 0, 255, self._lower_brightness, self._upper_brightness)
                    if self.is_white_mode:
                        self._brightness = brightness
                    else:
                        if self.__is_color_rgb_encoded():
                            rgb = color_util.color_hsv_to_RGB(self._hs[0], self._hs[1], int(brightness * 100 / self._upper_brightness))
                            color = "{:02x}{:02x}{:02x}{:04x}{:02x}{:02x}".format(round(rgb[0]), round(rgb[1]), round(rgb[2]), round(self._hs[0]), round(self._hs[1] * 255 / 100), brightness)
                        else:
                            color = "{:04x}{:04x}{:04x}".format(round(self._hs[0]), round(self._hs[1] * 10.0), brightness)
                    self._hs = color
                    self._working_mode = MODE_COLOR

                if ATTR_HS_COLOR in kwargs:
                    if brightness is None:
                        brightness = self._brightness
                    hs = kwargs[ATTR_HS_COLOR]
                    if hs[1] == 0:
                        self._brightness = brightness
                        self._working_mode = MODE_WHITE
                    else:
                        if self.__is_color_rgb_encoded():
                            rgb = color_util.color_hsv_to_RGB(hs[0], hs[1], int(brightness * 100 / self._upper_brightness))
                            color = "{:02x}{:02x}{:02x}{:04x}{:02x}{:02x}".format(round(rgb[0]), round(rgb[1]), round(rgb[2]), round(hs[0]), round(hs[1] * 255 / 100), brightness)
                        else:
                            color = "{:04x}{:04x}{:04x}".format(round(hs[0]), round(hs[1] * 10.0), brightness)
                        self._hs = color
                        self._working_mode = MODE_COLOR

                if ATTR_COLOR_TEMP in kwargs:
                    if brightness is None:
                        brightness = self._brightness
                    mired = int(kwargs[ATTR_COLOR_TEMP])
                    if mired < self._min_mired:
                        mired = self._min_mired
                    elif mired > self._max_mired:
                        mired = self._max_mired
                    color_temp = int(self._upper_color_temp - (self._upper_color_temp / (self._max_mired - self._min_mired)) * (mired - self._min_mired))
                    self._working_mode = MODE_WHITE
                    self._brightness = brightness
                    self._color_temp = color_temp

                self._device.set_multiple_values({
                    '20': self._is_on,
                    '21': self._working_mode,
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