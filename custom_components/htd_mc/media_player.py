"""Support for HTD MC Series"""
import logging

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import (
    MediaPlayerEntityFeature
)
from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)

from custom_components.htd_mc import HtdConstants
from htd_mc_client.models import ZoneDetail
from . import DOMAIN

SUPPORT_HTD_MC = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_entities, discovery_info=None):
    htd_configs = hass.data[DOMAIN]
    entities = []

    for device_index in range(len(htd_configs)):
        config = htd_configs[device_index]
        zones = config['zones']
        client = config['client']
        sources = config['sources']

        for zone_index in range(len(zones)):
            entity = HtdDevice(device_index, client, sources, zone_index + 1, zones[zone_index])
            entities.append(entity)

    add_entities(entities)


class HtdDevice(MediaPlayerEntity):
    device_instance_id = None
    client = None
    sources = None
    zone = None
    changing_volume = None
    zone_info = None

    def __init__(self, device_instance_id, client, sources, zone, zone_name):
        self.device_instance_id = device_instance_id
        self.client = client
        self.sources = sources
        self.zone = zone
        self.zone_name = zone_name
        self.update()

    @property
    def enabled(self) -> bool:
        return self.zone_info is not None

    @property
    def supported_features(self):
        return SUPPORT_HTD_MC

    @property
    def unique_id(self):
        return f'media_player.htd_mc_zone_{self.device_instance_id}_{self.zone}'

    @property
    def name(self):
        return self.zone_name

    def update(self):
        _LOGGER.debug("starting updating zone %d" % self.zone)
        self.zone_info = self.client.query_zone(self.zone)
        _LOGGER.debug("got new update for Zone %d, zone_info = %s" % (self.zone, self.zone_info))

    @property
    def state(self):
        if self.zone_info.power is None:
            return STATE_UNKNOWN
        if self.zone_info.power:
            return STATE_ON
        return STATE_OFF

    def turn_on(self):
        self.client.power_on(self.zone)

    def turn_off(self):
        self.client.power_off(self.zone)

    @property
    def volume_level(self):
        # volume from this client comes in as 1 - 100, home assistant want's a decimal between 0 and 1.
        return self.zone_info.volume / 100

    def set_volume_level(self, new_volume):
        if self.changing_volume is not None:
            _LOGGER.info("changing new desired volume for zone %d to %d" % (self.zone, new_volume))
            self.changing_volume = new_volume * 100
            return

        def on_progress(desired: int, zone_info: ZoneDetail) -> int | None:
            self.zone_info = zone_info
            self.schedule_update_ha_state()
            _LOGGER.info('updated zone = %d, desired = %f, current = %f' % (self.zone, desired, self.zone_info.volume))

            if desired != self.changing_volume:
                _LOGGER.info("a new volume for zone %d has been chosen, value = %d" % (self.zone, self.changing_volume))
                return self.changing_volume

            return None

        self.changing_volume = new_volume * 100
        self.client.set_volume(self.zone, self.changing_volume, on_progress)
        self.changing_volume = None
        self.schedule_update_ha_state()

    @property
    def is_volume_muted(self):
        return self.zone_info.mute

    def mute_volume(self, mute):
        self.client.toggle_mute(self.zone)

    @property
    def source(self):
        return self.sources[self.zone_info.source - 1]

    @property
    def source_list(self):
        return self.sources

    @property
    def media_title(self):
        return self.source

    def select_source(self, source):
        index = self.sources.index(source)
        self.client.set_source(self.zone, index + 1)

    @property
    def icon(self):
        return 'mdi:disc-player'
