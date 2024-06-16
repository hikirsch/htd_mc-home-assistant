class HtdConstants:
    # the first and second data bits are always this. whether we send or receive.
    FIRST_DATA_BIT = 0x02
    SECOND_DATA_BIT = 0x00

    # in order to not flood the device with commands, we have a delay inbetween commands, in milliseconds
    DEFAULT_COMMAND_DELAY = 100

    # the device is flakey, let's retry a few times
    DEFAULT_RETRY_ATTEMPTS = 3

    # the port of the device, default is 10006
    DEFAULT_HTD_MC_PORT = 10006

    # the number of seconds before we give up trying to read from the device
    DEFAULT_SOCKET_TIMEOUT = 1

    # 255 is the max value you can have with 1 byte. the volume max is 60.
    # so, we use 256 to represent a real 100% when computing the volume
    MAX_HTD_RAW_VOLUME = 256
    MAX_HTD_VOLUME = 60
    MAX_HTD_ZONES = 6
    VOLUME_OFFSET = MAX_HTD_RAW_VOLUME - MAX_HTD_VOLUME

    # each message we get is chunked at 14 bytes
    MESSAGE_CHUNK_SIZE = 14

    # command codes instruct the device what mode to do, it's follow with a command as well listed below
    SET_COMMAND_CODE = 0x04
    QUERY_COMMAND_CODE = 0x06

    # commands to be used for SET_COMMAND_CODE
    POWER_OFF_ZONE_COMMAND = 0x21
    POWER_ON_ZONE_COMMAND = 0x20
    POWER_ON_ALL_ZONES_COMMAND = 0x38
    POWER_OFF_ALL_ZONES_COMMAND = 0x39
    TOGGLE_MUTE_COMMAND = 0x22
    VOLUME_UP_COMMAND = 0x09
    VOLUME_DOWN_COMMAND = 0x0A
    BASE_UP_COMMAND = 0x26
    BASE_DOWN_COMMAND = 0x27
    TREBLE_UP_COMMAND = 0x28
    TREBLE_DOWN_COMMAND = 0x29
    BALANCE_RIGHT_COMMAND = 0x2A
    BALANCE_LEFT_COMMAND = 0x2B

    # the byte index for where to locate the corresponding setting
    ZONE_NUMBER_ZONE_DATA_INDEX = 2
    STATE_TOGGLES_ZONE_DATA_INDEX = 4
    SOURCE_ZONE_DATA_INDEX = 8
    VOLUME_ZONE_DATA_INDEX = 9
    TREBLE_ZONE_DATA_INDEX = 10
    BASS_ZONE_DATA_INDEX = 11
    BALANCE_ZONE_DATA_INDEX = 12

    # state toggles represent on and off values only. they are all stored within one byte. each binary digit is
    # treated as a flag. these are indexes of each state toggle
    POWER_STATE_TOGGLE_INDEX = 0
    MUTE_STATE_TOGGLE_INDEX = 1
    MODE_STATE_TOGGLE_INDEX = 2
    PARTY_MODE_STATE_TOGGLE_INDEX = 3
