class ZoneDetail:
    number: int = None
    power: bool = None
    mute: bool = None
    mode: bool = None
    party: bool = None
    source: int = None
    volume: int = None
    htd_volume: int = None
    treble: int = None
    bass: int = None
    balance: int = None

    def __init__(self, number: int):
        self.number = number
