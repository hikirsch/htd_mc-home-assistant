"""Support for HTD MC Series"""
from homeassistant.components.media_player import PLATFORM_SCHEMA, MediaPlayerDevice
from homeassistant.components.media_player.const import (
    SUPPORT_SELECT_SOURCE,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    STATE_OFF,
    STATE_ON,
)

from . import DOMAIN, CONF_ZONES
from .htd_mc import HtdMcClient, MAX_HTD_VOLUME

SUPPORT_HTD_MC = (
    SUPPORT_SELECT_SOURCE
    | SUPPORT_TURN_OFF
    | SUPPORT_TURN_ON
    | SUPPORT_VOLUME_MUTE
    | SUPPORT_VOLUME_SET
    | SUPPORT_VOLUME_STEP
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    htd_config = hass.data[DOMAIN]
    zones = htd_config["zones"]
    host = htd_config["host"]
    port = htd_config["port"]
    sources = htd_config["sources"]

    entities = []
     
    for i in range(len(zones)):
        entities.append(HtdDevice(host, port, sources, i + 1, zones[i]))

    add_entities(entities)


class HtdDevice(MediaPlayerDevice):
    def __init__(self, host, port,  sources, zone, zone_name ):
        self.zone = zone
        self.zone_name = zone_name
        self.sources = sources
        self.client = HtdMcClient(host, port)

        self.update()

    @property
    def supported_features(self):
        return SUPPORT_HTD_MC

    @property
    def entity_id(self):
        return "media_player.zone_" + str(self.zone)

    @property
    def name(self):
        return self.zone_name

    def update(self):
        self.zone_info = self.client.query_zone(self.zone)

    @property
    def state(self):
        return STATE_ON if self.zone_info['power'] == 'on' else STATE_OFF

    def turn_on(self):
        self.client.set_power(self.zone, 1)

    def turn_off(self):
        self.client.set_power(self.zone, 0)

    @property
    def volume_level(self):
        return self.zone_info['vol'] / MAX_HTD_VOLUME

    def set_volume_level(self, new_volume):
        new_vol = int(MAX_HTD_VOLUME * new_volume)
        self.client.set_volume(self.zone, new_vol)

    @property
    def is_volume_muted(self):
        return self.zone_info["mute"] == "on"

    def mute_volume(self, mute):
        self.client.toggle_mute(self.zone)

    @property
    def source(self):
        return self.sources[self.zone_info["source"] - 1]

    @property
    def source_list(self):
        return self.sources

    @property
    def media_title(self):
        return self.source

    def select_source(self, source):
        index = self.sources.index(source)
        self.client.set_source(self.zone, index + 1)