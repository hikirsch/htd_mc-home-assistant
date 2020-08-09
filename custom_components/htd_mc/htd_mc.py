import socket
import time
import logging

MAX_HTD_VOLUME = 60
DEFAULT_HTD_MC_PORT = 10006

_LOGGER = logging.getLogger(__name__)


def to_correct_string(message):
    string = ""
    for i in range(len(message)):
        string += hex(message[i]) + ","
    return string[:-1]


class HtdMcClient:
    def __init__(self, ip_address, port=DEFAULT_HTD_MC_PORT):
        self.ip_address = ip_address
        self.port = port
        self.zones = {
            k: {
                'zone': k,
                'power': None,
                'input': None,
                'vol': None,
                'mute': None,
                'source': None,
            } for k in range(1, 7)
        }

    def parse(self, cmd, message, zone_number):
        if len(message) > 14:
            zones = list()
            # each chunk represents a different zone that should be 14 bytes long,
            # query_all should work for each zone but doesn't, so we only take the first chunk

            # zone0 = message[0:14]
            zone1 = message[14:28]
            zone2 = message[28:42]
            zone3 = message[42:56]
            zone4 = message[56:70]
            zone5 = message[70:84]
            zone6 = message[84:98]

            # again, in a real working world situation, each zone would be correctly populated but we only ever work with 1 and whatever we get back.
            zones.append(zone1)
            zones.append(zone2)
            zones.append(zone3)
            zones.append(zone4)
            zones.append(zone5)
            zones.append(zone6)

            # go through each zone
            for i in zones:
                success = self.parse_message(cmd, i, zone_number) or success

            if not success:
                _LOGGER.warning(f"Update for Zone #{zone_number} failed.")

        elif len(message) == 14:
            self.parse_message(cmd, message, zone_number)

        if zone_number is None:
            return self.zones

        return self.zones[zone_number]

    def parse_message(self, cmd, message, zone_number):
        if len(message) != 14:
            return False

        zone = message[2]

        # it seems that even though we send one zone we may not get what we want
        if zone in range(1, 7):
            self.zones[zone]['power'] = "on" if (
                message[4] & 1 << 7) >> 7 else "off"
            self.zones[zone]['source'] = message[8] + 1
            self.zones[zone]['vol'] = message[9] - 196 if message[9] else 0
            self.zones[zone]['mute'] = "on" if (
                message[4] & 1 << 6) >> 6 else "off"

            _LOGGER.debug(
                f"Command for Zone #{zone} retrieved (requested #{zone_number}) --> Cmd = {to_correct_string(cmd)} | Message = {to_correct_string(message)}")

            return True
        else:
            _LOGGER.warning(
                f"Sent command for Zone #{zone_number} but got #{zone} --> Cmd = {to_correct_string(cmd)} | Message = {to_correct_string(message)}")

        return False

    def set_source(self, zone, input):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        if input not in range(1, 7):
            _LOGGER.warning("invalid input number")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, input + 2])

        self.send_command(cmd, zone)

    def volume_up(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x09])
        self.send_command(cmd, zone)

    def volume_down(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x0A])
        self.send_command(cmd, zone)

    def set_volume(self, zone, vol):
        if vol not in range(0, MAX_HTD_VOLUME):
            _LOGGER.warning("Invald Volume")
            return

        zone_info = self.query_zone(zone)

        vol_diff = vol - zone_info['vol']
        start_time = time.time()

        if vol_diff < 0:
            for k in range(abs(vol_diff)):
                self.volume_down(zone)
        elif vol_diff > 0:
            for k in range(vol_diff):
                self.volume_up(zone)
        else:
            pass

        return

    def toggle_mute(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x22])
        self.send_command(cmd, zone)

    def query_zone(self, zone):
        if zone not in range(1, 7):
            _LOGGER.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x06, 0x00])
        return self.send_command(cmd, zone)

    def query_all(self):
        cmd = bytearray([0x02, 0x00, 0x00, 0x05, 0x00])
        return self.send_command(cmd)

    def set_power(self, zone, pwr):
        if zone not in range(0, 7):
            _LOGGER.warning("Invalid Zone")
            return

        if pwr not in [0, 1]:
            _LOGGER.warning("invalid power command")
            return

        if zone == 0:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x38 if pwr else 0x39])
        else:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x20 if pwr else 0x21])

        self.send_command(cmd, zone)

    def send_command(self, cmd, zone=None):
        cmd.append(self.checksum(cmd))
        mySocket = socket.socket()
        mySocket.settimeout(.5)
        try:
            mySocket.connect((self.ip_address, self.port))
            mySocket.send(cmd)
            data = mySocket.recv(1024)
            _LOGGER.debug(f"Command = {cmd} | Response = {data} ")
            mySocket.close()

            return self.parse(cmd, data, zone)
        except socket.timeout:
            return self.unknown_response(cmd, zone)

    def unknown_response(self, cmd, zone):
        for zone in range(1, 7):
            self.zones[zone]['power'] = "unknown"
            self.zones[zone]['source'] = 0
            self.zones[zone]['vol'] = 0
            self.zones[zone]['mute'] = "unknown"

        return self.zones[zone]

    def checksum(self, message):
        cs = 0
        for b in message:
            cs += b
        csb = cs & 0xff
        return cs
