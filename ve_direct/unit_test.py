import unittest
from .parser import VEDirectParser, Event, TextEvent, FrameEndEvent


class TestVEDirectParser(unittest.TestCase):
    maxDiff = None
    
    MPPT_SAMPLE = b'\r\nPID\t0xA042\r\nFW\t116\r\nSER#\tHQ1636WR7KW\r\nV\t11020' + \
        b'\r\nI\t0\r\nVPV\t12300\r\nPPV\t0\r\nCS\t0\r\nERR\t0\r\nLOAD\tON\r\nIL\t0' + \
        b'\r\nH19\t327\r\nH20\t0\r\nH21\t0\r\nH22\t0\r\nH23\t0\r\nHSDS\t35\r\nChecksum\tr'

    MPPT_SAMPLE_FIELDS: list[Event] = [
        TextEvent("PID", "0xA042"),
        TextEvent("FW", "116"),
        TextEvent("SER#", "HQ1636WR7KW"),
        TextEvent("V", "11020"),
        TextEvent("I", "0"),
        TextEvent("VPV", "12300"),
        TextEvent("PPV", "0"),
        TextEvent("CS", "0"),
        TextEvent("ERR", "0"),
        TextEvent("LOAD", "ON"),
        TextEvent("IL", "0"),
        TextEvent("H19", "327"),
        TextEvent("H20", "0"),
        TextEvent("H21", "0"),
        TextEvent("H22", "0"),
        TextEvent("H23", "0"),
        TextEvent("HSDS", "35"),
        FrameEndEvent(True)
    ]

    def test_single_frame(self):
        vep = VEDirectParser()
        sample_fields = list(vep.receive_bytes(self.MPPT_SAMPLE))
        self.assertEqual(sample_fields, self.MPPT_SAMPLE_FIELDS)
