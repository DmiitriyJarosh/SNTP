import datetime
import struct
import time

SYSTEM_ZERO_TIME = datetime.date(*time.gmtime(0)[0:3])
NTP_ZERO_TIME = datetime.date(1900, 1, 1)
ZERO_TIME_DELTA = (SYSTEM_ZERO_TIME - NTP_ZERO_TIME).days * 24 * 3600


def get_frac_part(timestamp, n=32):
    return int(abs(timestamp - int(timestamp)) * 2 ** n)


# build timestamp from fractional and integral parts
def build_timestamp(integral, fractional):
    return integral + float(fractional) / 2 ** 32


class Packet:
    packet_byte_format = "!B B B b 11I"

    def __init__(self, version=2, mode=3, transmit_time=0, data=None):
        # if we add or take extra second (0 - nothing)
        self.leap = 0
        # version of protocol
        self.version = version
        # mode of node - it will be server (mode == 3)
        self.mode = mode
        # level of server (how far from atomic watch)
        self.stratum = 0
        # ask interval
        self.poll = 0
        # watch precision (our will be 1000 updates in sec)
        self.precision = -10
        # time for time travel from watches to server
        self.root_delay = 0
        # time dispersion
        self.root_dispersion = 0
        # identifier of watches
        self.ref_id = 0
        # time from watches
        self.reference_time = 0
        # time of sending this query (copied from ask-packet)
        self.originate_time = 0
        self.originate_time_high = 0
        self.originate_time_low = 0

        # time when packet was received by server
        self.received_time = 0

        # rime when packet was sent by server
        self.transmit_time = transmit_time
        self.transmit_time_high = 0
        self.transmit_time_low = 0

        if data is not None:
            self.from_bytes(data)

    # convert packet object to bytes
    def bytes(self):
        packed = struct.pack(
            Packet.packet_byte_format,
            self.leap << 6 | self.version << 3 | self.mode,
            self.stratum,
            self.poll,
            self.precision,
            int(self.root_delay) << 16 | get_frac_part(self.root_delay, 16),
            int(self.root_dispersion) << 16 | get_frac_part(self.root_dispersion, 16),
            self.ref_id,
            int(self.reference_time),
            get_frac_part(self.reference_time),
            self.originate_time_high,
            self.originate_time_low,
            int(self.received_time),
            get_frac_part(self.received_time),
            int(self.transmit_time),
            get_frac_part(self.transmit_time)
        )
        return packed

    # fill fields of object from bytes
    def from_bytes(self, data):
        unpacked = struct.unpack(Packet.packet_byte_format, data[0:struct.calcsize(Packet.packet_byte_format)])

        self.leap = unpacked[0] >> 6 & 0x3
        self.version = unpacked[0] >> 3 & 0x7
        self.mode = unpacked[0] & 0x7
        self.stratum = unpacked[1]
        self.poll = unpacked[2]
        self.precision = unpacked[3]
        self.root_delay = float(unpacked[4]) / 2 ** 16
        self.root_dispersion = float(unpacked[5]) / 2 ** 16
        self.ref_id = unpacked[6]
        self.reference_time = build_timestamp(unpacked[7], unpacked[8])
        self.originate_time = build_timestamp(unpacked[9], unpacked[10])
        self.originate_time_high = unpacked[9]
        self.originate_time_low = unpacked[10]
        self.received_time = build_timestamp(unpacked[11], unpacked[12])
        self.transmit_time = build_timestamp(unpacked[13], unpacked[14])
        self.transmit_time_high = unpacked[13]
        self.transmit_time_low = unpacked[14]
