import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

DOMAIN = "ledvance_orbis"
_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    """Bileşeni başlatır."""
    _LOGGER.info("Ledvance Orbis bileşeni başlatıldı")
    hass.data[DOMAIN] = {}
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Config flow ile eklenen bileşenleri ayarlar."""
    hass.data[DOMAIN][entry.entry_id] = entry.data
    _LOGGER.info("Ledvance Orbis cihazı eklendi: %s", entry.data)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Config flow ile eklenen bileşen kaldır"""