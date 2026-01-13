"""Tests for protocol parser."""

from floocast.protocol.messages import FlooMsgOk
from floocast.protocol.parser import FlooParser


class TestFlooParser:
    def test_msg_headers_contains_ok(self):
        assert "OK" in FlooParser.MSG_HEADERS

    def test_msg_headers_contains_st(self):
        assert "ST" in FlooParser.MSG_HEADERS

    def test_msg_headers_contains_ac(self):
        assert "AC" in FlooParser.MSG_HEADERS

    def test_header_maps_to_create_valid_msg(self):
        creator = FlooParser.MSG_HEADERS.get("ST")
        assert creator is not None
        msg = creator(b"ST=06")
        assert msg is not None
        assert msg.state == 6

    def test_ok_header_creator(self):
        creator = FlooParser.MSG_HEADERS.get("OK")
        msg = creator(b"OK")
        assert msg is not None
        assert isinstance(msg, FlooMsgOk)
