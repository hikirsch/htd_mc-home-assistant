import logging
import socket
import time

from .constants import HtdConstants
from .models import ZoneDetail
from .utils import get_command, parse_message, validate_source, validate_zone

_LOGGER = logging.getLogger(__name__)

MAX_BYTES_TO_RECEIVE = 2 ** 10  # 1024
ONE_SECOND = 1_000


class HtdMcClient:
    ip_address: str = None
    port: int = None
    command_delay_sec: float = None
    retry_attempts: int = None
    socket_timeout: float = None

    def __init__(
        self,
        ip_address: str,
        port: int = HtdConstants.DEFAULT_HTD_MC_PORT,
        command_delay: int = HtdConstants.DEFAULT_COMMAND_DELAY,
        retry_attempts: int = HtdConstants.DEFAULT_RETRY_ATTEMPTS,
        socket_timeout: int = HtdConstants.DEFAULT_SOCKET_TIMEOUT,
    ):
        self.ip_address = ip_address
        self.port = port
        self.command_delay_sec = command_delay / ONE_SECOND
        self.retry_attempts = retry_attempts
        self.socket_timeout = socket_timeout

    def query_zone(self, zone: int) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(zone, HtdConstants.QUERY_COMMAND_CODE, 0)

    def set_source(self, zone: int, source: int) -> ZoneDetail | None:
        validate_zone(zone)
        validate_source(source)

        # I have no idea why this is offset by 2
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            source + 2
        )

    def volume_up(self, zone: int) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.VOLUME_UP_COMMAND
        )

    def volume_down(self, zone: int) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            HtdConstants.VOLUME_DOWN_COMMAND
        )

    def set_volume(
        self, zone: int, volume: float, on_increment=None, zone_info=None
    ) -> ZoneDetail | None:
        if zone_info is None:
            zone_info = self.query_zone(zone)

        diff = round(volume) - zone_info.volume

        if 1 >= diff >= -1:
            return zone_info

        if diff < 0:
            zone_info = self.volume_down(zone)
        else:
            zone_info = self.volume_up(zone)

        if zone_info is None:
            zone_info = self.query_zone(zone)

        if on_increment is not None:
            override_volume = on_increment(volume, zone_info)

            if override_volume is not None:
                volume = override_volume

        return self.set_volume(zone, volume, on_increment, zone_info)

    def toggle_mute(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            HtdConstants.TOGGLE_MUTE_COMMAND
        )

    def power_on(self, zone=None, all_zones=False) -> ZoneDetail | None:
        if all_zones:
            zone = 1  # zone is one when it's all zones
            power_command = HtdConstants.POWER_ON_ALL_ZONES_COMMAND
        else:
            validate_zone(zone)
            power_command = HtdConstants.POWER_ON_ZONE_COMMAND
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            power_command
        )

    def power_off(self, zone=None, all_zones=False) -> ZoneDetail | None:
        if all_zones:
            zone = 1  # zone is one when it's all zones
            power_command = HtdConstants.POWER_OFF_ALL_ZONES_COMMAND
        else:
            validate_zone(zone)
            power_command = HtdConstants.POWER_OFF_ZONE_COMMAND
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            power_command
        )

    def bass_up(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BASE_UP_COMMAND
        )

    def bass_down(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BASE_DOWN_COMMAND
        )

    def treble_up(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.TREBLE_UP_COMMAND
        )

    def treble_down(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            HtdConstants.TREBLE_DOWN_COMMAND
        )

    def balance_right(self, zone) -> ZoneDetail | None:
        validate_zone(zone)
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            HtdConstants.BALANCE_RIGHT_COMMAND
        )

    def balance_left(self, zone):
        validate_zone(zone)
        return self.send_command(
            zone,
            HtdConstants.SET_COMMAND_CODE,
            HtdConstants.BALANCE_LEFT_COMMAND
        )

    def get_model_info(self):
        return self.send_command(1, HtdConstants.MODEL_QUERY_COMMAND_CODE, 0)

    def send_command(
        self, zone, command, data_code, attempt=0
    ) -> ZoneDetail | str | None:
        cmd = get_command(zone, command, data_code)

        address = (self.ip_address, self.port)
        connection = socket.create_connection(address)
        connection.settimeout(self.socket_timeout)
        connection.send(cmd)
        data = connection.recv(MAX_BYTES_TO_RECEIVE)
        connection.close()
        time.sleep(self.command_delay_sec)

        if command is HtdConstants.MODEL_QUERY_COMMAND_CODE:
            return data.decode("utf-8")

        response = parse_message(zone, data)

        if response is None and attempt < self.retry_attempts:
            _LOGGER.warning(
                "Bad response, will retry. zone = %d, retry = %d" % (
                    zone, attempt)
            )
            time.sleep(
                (self.command_delay_sec * 2) * (attempt + 1)
            )  # sleep longer each time to be sure.
            return self.send_command(zone, command, data_code, attempt + 1)

        if response is None:
            _LOGGER.critical(
                (
                    "Still bad response after retrying! zone = %d! "
                    "Consider increasing your command_delay!"
                )
                % zone
            )

        return response
