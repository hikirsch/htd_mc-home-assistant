"""Support for Home Theatre Direct's MC series"""

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery
from homeassistant.helpers.typing import ConfigType

from .htd_mc_client.client import HtdMcClient
from .htd_mc_client.constants import HtdConstants

DOMAIN = "htd_mc"

CONF_ZONES = "zones"
CONF_SOURCES = "sources"
CONF_RETRY_ATTEMPTS = "retry_attempts"
CONF_SOCKET_TIMEOUT = "socket_timeout"
CONF_COMMAND_DELAY = "command_delay"
CONF_UPDATE_VOLUME_ON_CHANGE = "update_volume_on_change"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            [
                {
                    vol.Required(CONF_HOST): cv.string,
                    vol.Optional(
                        CONF_PORT, default=HtdConstants.DEFAULT_HTD_MC_PORT
                    ): cv.port,
                    vol.Optional(CONF_ZONES): vol.All(
                        cv.ensure_list,
                        [cv.string]
                    ),
                    vol.Optional(CONF_SOURCES): vol.All(
                        cv.ensure_list,
                        [cv.string]
                    ),
                    vol.Optional(
                        CONF_RETRY_ATTEMPTS,
                        default=HtdConstants.DEFAULT_RETRY_ATTEMPTS
                    ): cv.port,
                    vol.Optional(
                        CONF_SOCKET_TIMEOUT,
                        default=HtdConstants.DEFAULT_SOCKET_TIMEOUT
                    ): cv.port,
                    vol.Optional(
                        CONF_COMMAND_DELAY,
                        default=HtdConstants.DEFAULT_COMMAND_DELAY
                    ): cv.port,
                    vol.Optional(CONF_UPDATE_VOLUME_ON_CHANGE): cv.boolean,
                }
            ]
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass: HomeAssistant, config: ConfigType):
    htd_config = config.get(DOMAIN)

    configs = []

    for i in range(len(htd_config)):
        htd_item_config = htd_config[i]
        host = htd_item_config.get(CONF_HOST)
        port = htd_item_config.get(CONF_PORT)
        zones = htd_item_config.get(CONF_ZONES)
        sources = htd_item_config.get(CONF_SOURCES)
        retry_attempts = htd_item_config.get(CONF_RETRY_ATTEMPTS)
        command_delay = htd_item_config.get(CONF_COMMAND_DELAY)
        socket_timeout = htd_item_config.get(CONF_SOCKET_TIMEOUT)
        update_volume_on_change = htd_item_config.get(
            CONF_UPDATE_VOLUME_ON_CHANGE
        )

        if zones is None:
            zones = []

        if sources is None:
            sources = []

        # the device has 6 zones, so we default to Zone X
        for i in range(len(zones), 6):
            zones.append("Zone " + str(i + 1))

        # the device has 6 sources, so we default to Source X
        for i in range(len(sources), 6):
            sources.append("Source " + str(i + 1))

        client = HtdMcClient(
            host,
            port=port,
            command_delay=command_delay,
            retry_attempts=retry_attempts,
            socket_timeout=socket_timeout,
        )

        configs.append(
            {
                "zones": zones,
                "sources": sources,
                "client": client,
                "update_volume_on_change": update_volume_on_change,
            }
        )

    hass.data[DOMAIN] = configs

    for component in ("media_player",):
        discovery.load_platform(hass, component, DOMAIN, {}, config)

    return True
