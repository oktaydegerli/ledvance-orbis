import logging
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    ATTR_HS_COLOR,
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_HS,
    LightEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from tinytuya import BulbDevice

from .const import CONF_IP_ADDRESS, CONF_DEVICE_ID, CONF_LOCAL_KEY, DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    config = hass.data[DOMAIN][config_entry.entry_id]
    device = BulbDevice(
        config[CONF_DEVICE_ID],
        config[CONF_IP_ADDRESS],
        config[CONF_LOCAL_KEY],
    )
    async_add_entities([LedvanceOrbisLight(device)])

class LedvanceOrbisLight(LightEntity):
    def __init__(self, device):
        self._device = device
        self._name = device.name
        self._state = None
        self._brightness = None
        self._color_temp = None
        self._hs_color = None

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def brightness(self):
        return self._brightness

    @property
    def color_temp(self):
        return self._color_temp

    @property
    def hs_color(self):
        return self._hs_color

    @property
    def supported_color_modes(self):
        return {COLOR_MODE_COLOR_TEMP, COLOR_MODE_HS}

    @property
    def color_mode(self):
        if self._device.status()[21] == "white":
            return COLOR_MODE_COLOR_TEMP
        else:
            return COLOR_MODE_HS

    async def async_turn_on(self, **kwargs):
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
            await self._device.set_brightness(int(self._brightness * 10.23))

        if ATTR_COLOR_TEMP in kwargs:
            self._color_temp = kwargs[ATTR_COLOR_TEMP]
            await self._device.set_color_temp(int(self._color_temp))

        if ATTR_HS_COLOR in kwargs:
            self._hs_color = kwargs[ATTR_HS_COLOR]
            await self._device.set_colour(self._hs_color[0], self._hs_color[1])

        await self._device.turn_on()

    async def async_turn_off(self, **kwargs):
        await self._device.turn_off()

    async def async_update(self):
        status = self._device.status()
        self._state = status[20]
        self._brightness = int(status[22] / 10.23)
        self._color_temp = status[23]
        self._hs_color = self._device.colour()