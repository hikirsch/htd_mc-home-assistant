"""Support for HTD MC Series"""

import logging

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaPlayerEntityFeature
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from . import DOMAIN
from .htd_mc_client.client import HtdMcClient
from .htd_mc_client.models import ZoneDetail

MEDIA_PLAYER_PREFIX = "media_player.htd_mc_zone"

SUPPORT_HTD_MC = (
    MediaPlayerEntityFeature.SELECT_SOURCE
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_STEP
)

_LOGGER = logging.getLogger(__name__)


def setup_platform(hass: HomeAssistant, config, add_entities, discovery_info=None):
    htd_configs = hass.data[DOMAIN]
    entities = []

    for device_index in range(len(htd_configs)):
        config = htd_configs[device_index]
        zones = config["zones"]
        client = config["client"]

        for zone_index in range(len(zones)):
            entity = HtdDevice(device_index, zone_index + 1, client, config)
            entities.append(entity)

    add_entities(entities)


class HtdDevice(MediaPlayerEntity):
    device_instance_id: int = None
    client: HtdMcClient = None
    sources: [str] = None
    zone: int = None
    changing_volume: int | None = None
    zone_info: ZoneDetail = None

    def __init__(self, device_instance_id, zone, client, config):
        self.device_instance_id = device_instance_id
        self.zone = zone
        self.client = client
        self.sources = config["sources"]
        self.update_volume_on_change = config["update_volume_on_change"]
        # zones are 0 based in the config b/c it's an array
        self.zone_name = config["zones"][zone - 1]
        self.update()

    @property
    def enabled(self) -> bool:
        return self.zone_info is not None

    @property
    def supported_features(self):
        return SUPPORT_HTD_MC

    @property
    def unique_id(self):
        return f"{MEDIA_PLAYER_PREFIX}_{self.device_instance_id}_{self.zone}"

    @property
    def name(self):
        return self.zone_name

    def update(self):
        _LOGGER.debug("starting updating zone %d" % self.zone)
        self.zone_info = self.client.query_zone(self.zone)
        _LOGGER.debug(
            "got new update for Zone %d, zone_info = %s" % (self.zone, self.zone_info)
        )

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
    def volume_level(self) -> float:
        # volume from this client comes in as 1 - 100,
        # home assistant wants a decimal between 0 and 1.
        return self.zone_info.volume / 100

    def set_volume_level(self, new_volume: float):
        if self.changing_volume is not None:
            _LOGGER.info(
                "changing new desired volume for zone %d to %d"
                % (self.zone, new_volume)
            )
            self.changing_volume = int(new_volume * 100)
            return

        def on_increment(desired: int, zone_info: ZoneDetail) -> int | None:
            if self.update_volume_on_change:
                self.zone_info = zone_info
                self.schedule_update_ha_state()

            _LOGGER.info(
                "updated zone = %d, desired = %f, current = %f"
                % (self.zone, desired, self.zone_info.volume)
            )

            if desired != self.changing_volume:
                _LOGGER.info(
                    "a new volume for zone %d has been chosen, value = %d"
                    % (self.zone, self.changing_volume)
                )
                return self.changing_volume

            return None

        self.changing_volume = int(new_volume * 100)
        self.client.set_volume(self.zone, self.changing_volume, on_increment)
        self.changing_volume = None
        self.schedule_update_ha_state()

    @property
    def is_volume_muted(self) -> bool:
        return self.zone_info.mute

    def mute_volume(self, mute):
        self.client.toggle_mute(self.zone)

    @property
    def source(self) -> int:
        return self.sources[self.zone_info.source - 1]

    @property
    def source_list(self):
        return self.sources

    @property
    def media_title(self):
        return self.source

    def select_source(self, source: int):
        index = self.sources.index(source)
        self.client.set_source(self.zone, index + 1)

    @property
    def icon(self):
        return "mdi:disc-player"
