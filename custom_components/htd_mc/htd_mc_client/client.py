import logging
import socket
import time

from constants import HtdConstants
from htd_mc_client.utils import validate_zone, validate_source, calculate_checksum, parse_message

_LOGGER = logging.getLogger(__name__)

# the device always seems to send 28 bytes.
MAX_BYTES_TO_RECEIVE = 2 ** 5  # 32
ONE_SECOND = 1_000


class HtdMcClient:
    ip_address: str = None
    port: int = None
    command_delay_sec: float = None
    retry_attempts: int = None
    socket_timeout: float = None

    def __init__(
        self,
        ip_address,
        port=HtdConstants.DEFAULT_HTD_MC_PORT,
        command_delay=HtdConstants.DEFAULT_COMMAND_DELAY,
        retry_attempts=HtdConstants.DEFAULT_RETRY_ATTEMPTS,
        socket_timeout=HtdConstants.DEFAULT_SOCKET_TIMEOUT,
    ):
        self.ip_address = ip_address
        self.port = port
        self.command_delay_sec = command_delay / ONE_SECOND
        self.retry_attempts = retry_attempts
        self.socket_timeout = socket_timeout

    def query_zone(self, zone):
        validate_zone(zone)
        return self.send_command(zone, HtdConstants.QUERY_COMMAND_CODE, 0)

    def set_source(self, zone, source):
        validate_zone(zone)
        validate_source(source)

        # I have no idea why this is offset by 2
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, source + 2)

    def volume_up(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.VOLUME_UP_COMMAND)

    def volume_down(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.VOLUME_DOWN_COMMAND)

    def set_volume(self, zone, volume, on_update=None, zone_info=None):
        if zone_info is None:
            zone_info = self.query_zone(zone)

        diff = round(volume) - zone_info.volume

        if on_update is not None:
            on_update(volume, diff)

        if 1 >= diff >= -1:
            return

        if diff < 0:
            self.volume_down(zone)
        else:
            self.volume_up(zone)

        self.set_volume(zone, volume, on_update)

    def toggle_mute(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.TOGGLE_MUTE_COMMAND)

    def power_on(self, zone=None, all_zones=False):
        if all_zones:
            zone = 1  # zone is one when it's all zones
            power_command = HtdConstants.POWER_ON_ALL_ZONES_COMMAND
        else:
            validate_zone(zone)
            power_command = HtdConstants.POWER_ON_ZONE_COMMAND
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, power_command)

    def power_off(self, zone=None, all_zones=False):
        if all_zones:
            zone = 1  # zone is one when it's all zones
            power_command = HtdConstants.POWER_OFF_ALL_ZONES_COMMAND
        else:
            validate_zone(zone)
            power_command = HtdConstants.POWER_OFF_ZONE_COMMAND
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, power_command)

    def bass_up(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BASE_UP_COMMAND)

    def bass_down(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BASE_DOWN_COMMAND)

    def treble_up(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.TREBLE_UP_COMMAND)

    def treble_down(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.TREBLE_DOWN_COMMAND)

    def balance_right(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BALANCE_RIGHT_COMMAND)

    def balance_left(self, zone):
        validate_zone(zone)
        self.send_command(zone, HtdConstants.SET_COMMAND_CODE, HtdConstants.BALANCE_LEFT_COMMAND)

    def send_command(self, zone, command, data_code, attempt=0):
        cmd = bytearray([HtdConstants.FIRST_DATA_BIT, HtdConstants.SECOND_DATA_BIT, zone, command, data_code])
        checksum = calculate_checksum(cmd)
        cmd.append(checksum)

        address = (self.ip_address, self.port)
        connection = socket.create_connection(address)
        connection.settimeout(self.socket_timeout)
        connection.send(cmd)
        data = connection.recv(MAX_BYTES_TO_RECEIVE)
        connection.close()

        time.sleep(self.command_delay_sec)

        response = parse_message(data)

        if response is None and attempt < self.retry_attempts:
            _LOGGER.warning('Bad response, will retry. zone = %d, retry = %d' % (zone, attempt))
            time.sleep(self.command_delay_sec * (attempt + 1))  # sleep longer each time to be sure.
            return self.send_command(zone, command, data_code, attempt + 1)

        return response
