
from __future__ import absolute_import, division, print_function
import socket
import time, logging

MAX_HTD_VOLUME = 60
DEFAULT_HTD_MC_PORT = 10006

class HtdMcClient:
    def __init__(self, ip_address, port=DEFAULT_HTD_MC_PORT):
        self.ip_address = ip_address
        self.port = port
        self.zonelist = {
            k + 1: {
                # 'name': self.zone_names[k],
                'power': None,
                'input': None,
                'vol': None,
                'mute': None,
                'source': None,
            } for k in range(6)
        }

    def checksum(self, message):
        cs = 0
        for b in message:
            cs = cs + b
        csb = cs & 0xff
        return csb

    def parse_reply(self, message, zone_number):
        if len(message) > 14:
            zone_List = list()
            # zone0 = message[0:14]
            zone1 = message[14:28]
            zone2 = message[28:42]
            zone3 = message[42:56]
            zone4 = message[56:70]
            zone5 = message[70:84]
            zone6 = message[84:98]
            zone_List.append(zone1)
            zone_List.append(zone2)
            zone_List.append(zone3)
            zone_List.append(zone4)
            zone_List.append(zone5)
            zone_List.append(zone6)
            for i in zone_List:
                if len(i) == 0:
                    continue

                zone = i[2]
                self.zonelist[zone]['power'] = "on" if (i[4] & 1 << 7) >> 7 else "off"
                self.zonelist[zone]['source'] = i[8] + 1
                self.zonelist[zone]['vol'] = i[9] - 196 if i[9] else 0
                self.zonelist[zone]['mute'] = "on" if (i[4] & 1 << 6) >> 6 else "off"
 
        if len(message) == 14:
            zone = message[2]
            self.zonelist[zone]['power'] = "on" if (message[4] & 1 << 7) >> 7 else "off"
            self.zonelist[zone]['source'] = message[8] + 1
            self.zonelist[zone]['vol'] = message[9] - 196 if message[9] else 0
            self.zonelist[zone]['mute'] = "on" if (message[4] & 1 << 6) >> 6 else "off"

        return self.zonelist[zone_number]

    def set_source(self, zone, input):
        if zone not in range(1, 7):
            logging.warning("Invalid Zone")
            return

        if input not in range(1, 7):
            logging.warning("invalid input number")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, input + 2])

        self.send_command(cmd, zone)

    def volume_up(self, zone):
        if zone not in range(1, 7):
            logging.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x09])
        self.send_command(cmd, zone)

    def volume_down(self, zone):
        if zone not in range(1, 7):
            logging.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x0A])
        self.send_command(cmd, zone)

    def set_volume(self, zone, vol):
        if vol not in range(0, MAX_HTD_VOLUME):
            logging.warning("Invald Volume")
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
            logging.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x04, 0x22])
        self.send_command(cmd, zone)

    def query_zone(self, zone):
        if zone not in range(1, 7):
            logging.warning("Invalid Zone")
            return

        cmd = bytearray([0x02, 0x00, zone, 0x06, 0x00])
        return self.send_command(cmd, zone)

    def set_power(self, zone, pwr):
        if zone not in range(0, 7):
            logging.warning("Invalid Zone")
            return

        if pwr not in [0, 1]:
            logging.warning("invalid power command")
            return

        if zone == 0:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x38 if pwr else 0x39])
        else:
            cmd = bytearray([0x02, 0x00, zone, 0x04, 0x20 if pwr else 0x21])

        self.send_command(cmd, zone)

    def send_command(self, cmd, zone):
        cmd.append(self.checksum(cmd))
        mySocket = socket.socket()
        mySocket.connect((self.ip_address, self.port))
        # print(cmd)
        mySocket.send(cmd)
        data = mySocket.recv(1024)
        mySocket.close()
        return self.parse_reply(data, zone)
