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

import logging
import json
from homeassistant.components.light import LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.color as color_util
import tinytuya
# from functools import partial
# import textwrap
# import asyncio

MODE_COLOR = "colour"
MODE_MUSIC = "music"
MODE_SCENE = "scene"
MODE_WHITE = "white"

SCENE_CUSTOM = "Custom"
SCENE_MUSIC = "Music"

SCENE_LIST = {
    "İyi Geceler": "AAABAQIODgAAyAAAAAA=",
    "Okuma Modu": "AAEBAQIODgAD6AH0AAA=",
    "Büyülü Orman": "AAcAAAEDA0tLAgB4AvgCJktLAgAzA+gD6EtLAgB4A+gBhg==",
    "Renk Modu": "AAQAAAEGA0ZGAQAAA+gD6EZGAQB4A+gD6EZGAQDwA+gD6EZGAQA9A+gD6EZGAQCuA+gD6EZGAQETA+gD6A==",
    "Sıcak Soğuk Mod": "AAUBAwJGRgED6AAKRkYBA+gBVEZGAQPoA+gAAA=",
    "Çöl Vahası": "AAgAAAEDA0tLAgAiAUoDNEtLAgAQArID6EtLAgAQA+gD6A==",
    "Pastel Rüyalar": "AAkAAAEDA0tLAgFLAMgD6EtLAgC0AQQDoktLAgAcAQ4D6A==",
    "Sonbahar Esintisi": "AAoAAAEDA0tLAgArA1IDUktLAgAAAyoCvEtLAgAnA+gD6A=",
    "Mistik Sular": "AAsAAAEDA0tLAgDDA+gD6EtLAgCgAfQD6EtLAgDwAwwBuA==",
    "Narenciye Sıçraması": "AAwAAAEDA0tLAgA8A+gD6EtLAgAnA+gD6EtLAgAQA+gD6A==",
    "Şehirde Uyanış": "AA0AAAEDA0tLAgAJAtAD6EtLAgAmASID6EtLAgAzA+gD6A==",
    "Tropikal Alacakaranlık": "AA8AAAEDA0tLAgFKAk4D6EtLAgAnA+gD6EtLAgC0A+gB9A==",
    "Gökkuşağı": "AB0AAAEGA0tLAgAAA+gD6EtLAgAnA+gD6EtLAgA8A+gD6EtLAgB4A+gD6EtLAgDSA+gD6EtLAgERA+gD6A=="
}

_LOGGER = logging.getLogger(__name__)

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

        self._state = False
        self._brightness = None
        self._color_temp = None
        self._color_mode = None
        self._color = None
        self._lower_brightness = 29
        self._upper_brightness = 1000
        self._upper_color_temp = self._upper_brightness
        self._max_mired = color_util.color_temperature_kelvin_to_mired(2700)
        self._min_mired = color_util.color_temperature_kelvin_to_mired(6500)

        self._hs = None
        self._effect = None
        self._effect_list = []
        self._scenes = None
        self._scenes = SCENE_LIST
        self._effect_list = list(self._scenes.keys())
        # self._effect_list.append(SCENE_MUSIC)

        self._name = "Ledvance Orbis"
        self._unique_id = f"ledvance_orbis_{device_id}"
        self._device = None

    async def async_init(self):
        def init_device():
            device = tinytuya.BulbDevice(dev_id=self._device_id, address=self._device_ip, local_key=self._local_key, version=3.3)
            return device
        self._device = await self.hass.async_add_executor_job(init_device)

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def is_on(self):
        return self._state
    
    @property
    def brightness(self):
        if self.is_color_mode or self.is_white_mode:
            return map_range(self._brightness, self._lower_brightness, self._upper_brightness, 0, 255)
        return None

    @property
    def hs_color(self):
        if self.is_color_mode:
            return self._hs
        return None

    @property
    def color_temp(self):
        if self.is_white_mode:
            return int(self._max_mired - (((self._max_mired - self._min_mired) / self._upper_color_temp) * self._color_temp))
        return None
    
    @property
    def min_mireds(self):
        return self._min_mired

    @property
    def max_mireds(self):
        return self._max_mired

    @property
    def effect(self):
        if self.is_scene_mode or self.is_music_mode:
            return self._effect
        return None

    @property
    def effect_list(self):
        return self._effect_list

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP | SUPPORT_COLOR | SUPPORT_EFFECT


    @property
    def is_white_mode(self):
        color_mode = self.__get_color_mode()
        return color_mode is None or color_mode == MODE_WHITE
    
    @property
    def is_color_mode(self):
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode == MODE_COLOR

    @property
    def is_scene_mode(self):
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode.startswith(MODE_SCENE)
    
    @property
    def is_music_mode(self):
        color_mode = self.__get_color_mode()
        return color_mode is not None and color_mode == MODE_MUSIC
    
    def __find_scene_by_scene_data(self, data):
        return next((item for item in self._effect_list if self._scenes.get(item) == data), SCENE_CUSTOM)
    
    def __get_color_mode(self):
        if self._color_mode is None:
            return MODE_WHITE
        else:
            return self._color_mode

    async def async_turn_on(self, **kwargs):
        def turn_on():
            if self._brightness is None:
                self._brightness = self._upper_brightness
            if self._color_temp is None:
                self._color_temp = self._upper_color_temp
            if self._color_mode is None:
                self._color_mode = MODE_WHITE
            self._effect = None
            try:
                if not self.is_on:
                    self._state = True

                if ATTR_EFFECT in kwargs:
                    if kwargs[ATTR_EFFECT] == SCENE_MUSIC:
                        self._color_mode = "music"
                    else:
                        self._color_mode = "scene"
                        self._effect = self._scenes.get(kwargs[ATTR_EFFECT])

                if ATTR_BRIGHTNESS in kwargs:
                    self._brightness = map_range(int(kwargs[ATTR_BRIGHTNESS]), 0, 255, self._lower_brightness, self._upper_brightness)
                    if not self.is_white_mode:
                        self._color = "{:04x}{:04x}{:04x}".format(round(self._hs[0]), round(self._hs[1] * 10.0), self._brightness)
                        self._color_mode = MODE_COLOR

                if ATTR_HS_COLOR in kwargs:
                    self._hs = kwargs[ATTR_HS_COLOR]
                    if self._hs[1] == 0:
                        self._color_mode = MODE_WHITE
                    else:
                        self._color = "{:04x}{:04x}{:04x}".format(round(self._hs[0]), round(self._hs[1] * 10.0), self._brightness)
                        self._color_mode = MODE_COLOR

                if ATTR_COLOR_TEMP in kwargs:
                    mired = int(kwargs[ATTR_COLOR_TEMP])
                    if mired < self._min_mired:
                        mired = self._min_mired
                    elif mired > self._max_mired:
                        mired = self._max_mired
                    self._color_temp = int(self._upper_color_temp - (self._upper_color_temp / (self._max_mired - self._min_mired)) * (mired - self._min_mired))
                    self._color_mode = MODE_WHITE

                states = {'20': True}

                if self._color_mode is not None:
                    states['21'] = self._color_mode

                if self._brightness is not None and self.is_white_mode:
                    states['22'] = self._brightness

                if self._color_temp is not None and self.is_white_mode:
                    states['23'] = self._color_temp

                if self._color is not None and self.is_color_mode:
                    states['24'] = self._color

                if self._effect is not None:
                    states['36'] = self._effect

                self._device.set_multiple_values(states)

                return True
            except Exception as e:
                _LOGGER.exception("Exception: %s", e)
                return False
            
        success = await self.hass.async_add_executor_job(turn_on)
        if success:
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        def turn_off():
            try:
                self._state = False
                self._device.set_multiple_values({'20': False})
                return True
            except Exception as e:
                return False

        success = await self.hass.async_add_executor_job(turn_off)
        if success:
            self.async_write_ha_state()