from .constants import HtdConstants
from .models import ZoneDetail


# convert the volume into a usable value. the device will transmit a number between 196 - 255.
# if it's at max volume, the raw volume will come as 0. this is probably because the gateway
# only transmits 8 bits per byte. 255 is 0b11111111. since there's no volume = 0 (use mute I guess),
# if the volume hits 0, it's because it's at max volume, so we make it 256.
# credit for this goes to lounsbrough
def convert_volume(raw_volume: int) -> (int, int):
    htd_volume = HtdConstants.MAX_HTD_VOLUME if raw_volume == 0 else raw_volume - HtdConstants.VOLUME_OFFSET
    percent_volume = round(htd_volume / HtdConstants.MAX_HTD_VOLUME * 100)
    fixed = max(0, min(100, percent_volume))
    return fixed, htd_volume


# the checksum is the last digit on the entire command, it's a sum of all the bytes.
def calculate_checksum(message) -> int:
    cs = 0
    for b in message:
        cs += b
    return cs


# helper method to check the state toggle index is on.
def is_bit_on(toggles: str, index: int) -> bool:
    return toggles[index] == '1'


# helper method to validate the source is not outside the range
def validate_source(source: int):
    if source not in range(1, HtdConstants.MAX_HTD_ZONES + 1):
        raise 'source %s is invalid' % source


# helper method to validate the zone is not outside the range
def validate_zone(zone: int):
    if zone not in range(1, HtdConstants.MAX_HTD_ZONES + 1):
        raise 'zone %s is invalid' % zone


# this will take a single message chunk of 14 bytes and parse this into a usable ZoneDetail model to read the state.
# all credit for this new parser goes to lounsbrough
def parse_zone(zone_data: bytes) -> ZoneDetail | None:
    if zone_data[0] != HtdConstants.FIRST_DATA_BIT and zone_data[1] != HtdConstants.SECOND_DATA_BIT:
        return None

    # I think this is some kind of verification, it's been right everytime so far.
    if zone_data[3] != 0x05:
        return None

    # the 4th position represent the toggles for power, mute, mode and party,
    state_toggles = get_state_toggles(zone_data[HtdConstants.STATE_TOGGLES_ZONE_DATA_INDEX])

    volume, htd_volume = convert_volume(zone_data[HtdConstants.VOLUME_ZONE_DATA_INDEX])

    zone_number = zone_data[HtdConstants.ZONE_NUMBER_ZONE_DATA_INDEX]

    zone = ZoneDetail(zone_number)

    zone.number = zone_number
    zone.power = is_bit_on(state_toggles, HtdConstants.POWER_STATE_TOGGLE_INDEX)
    zone.mute = is_bit_on(state_toggles, HtdConstants.MUTE_STATE_TOGGLE_INDEX)
    zone.mode = is_bit_on(state_toggles, HtdConstants.MODE_STATE_TOGGLE_INDEX)
    zone.party = is_bit_on(state_toggles, HtdConstants.PARTY_MODE_STATE_TOGGLE_INDEX)
    zone.source = zone_data[HtdConstants.SOURCE_ZONE_DATA_INDEX] + 1
    zone.volume = volume
    zone.htd_volume = htd_volume
    zone.treble = zone_data[HtdConstants.TREBLE_ZONE_DATA_INDEX]
    zone.bass = zone_data[HtdConstants.BASS_ZONE_DATA_INDEX]
    zone.balance = zone_data[HtdConstants.BALANCE_ZONE_DATA_INDEX]

    return zone


# the handler method to take the entire response from the controller and parse each zone. it was believed that the
# controller can respond with multiple zones. in my testing this has never been the case. the device will always send
# 28 bytes (2 chunks), the first chunk is always invalidated by some check, the second is zone info we requested. 
def parse_message(data: bytes) -> ZoneDetail | None:
    position = 0
    while position < len(data):
        # each chunk represents a different zone that should be 14 bytes long,
        zone_data = data[position:position + HtdConstants.MESSAGE_CHUNK_SIZE]
        position += HtdConstants.MESSAGE_CHUNK_SIZE

        # if the zone data we got is less than the exp
        if len(zone_data) < HtdConstants.MESSAGE_CHUNK_SIZE:
            break

        zone_info = parse_zone(zone_data)

        # if a valid zone was found, we're done
        if zone_info is not None:
            return zone_info

    return None


# helper method to convert the integer number for the state values into a binary string, so we can check the state
# of each individual toggle.
def get_state_toggles(raw_value: int):
    # the state toggles value needs to be interpreted in binary, each bit represents a new flag.
    state_toggles = bin(raw_value)

    # when converting to binary, python will prepend '0b', so substring starting at 2
    state_toggles = state_toggles[2:]

    # each of the 4 bits as 1 represent that the toggle is set to on, if it's less than 4 digits, we fill with zeros
    state_toggles = state_toggles.zfill(4)

    return state_toggles
