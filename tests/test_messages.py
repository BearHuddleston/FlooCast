"""Tests for protocol message classes."""

from floocast.protocol.messages import (
    FlooMessage,
    FlooMsgAc,
    FlooMsgBm,
    FlooMsgOk,
    FlooMsgPl,
    FlooMsgSt,
)


class TestFlooMessage:
    def test_send_message_format(self):
        msg = FlooMessage(True, "ST")
        assert msg.bytes == b"BC:ST\r\n"

    def test_send_message_with_payload(self):
        msg = FlooMessage(True, "ST", b"01")
        assert msg.bytes == b"BC:ST=01\r\n"

    def test_receive_message_format(self):
        msg = FlooMessage(False, "ST")
        assert msg.bytes == b"ST\r\n"


class TestFlooMsgOk:
    def test_create_valid_msg(self):
        msg = FlooMsgOk.create_valid_msg(b"OK")
        assert msg is not None
        assert msg.header == "OK"

    def test_create_invalid_msg(self):
        msg = FlooMsgOk.create_valid_msg(b"OKAY")
        assert msg is None


class TestFlooMsgSt:
    def test_create_valid_msg(self):
        msg = FlooMsgSt.create_valid_msg(b"ST=06")
        assert msg is not None
        assert msg.state == 6

    def test_create_invalid_msg(self):
        msg = FlooMsgSt.create_valid_msg(b"ST")
        assert msg is None

    def test_send_message(self):
        msg = FlooMsgSt(True, 0x06)
        assert b"BC:ST=06" in msg.bytes


class TestFlooMsgAc:
    def test_create_valid_msg_simple(self):
        msg = FlooMsgAc.create_valid_msg(b"AC=07")
        assert msg is not None
        assert msg.codec == 7

    def test_create_valid_msg_extended(self):
        msg = FlooMsgAc.create_valid_msg(b"AC=07,F0,0100")
        assert msg is not None
        assert msg.codec == 7
        assert msg.rssi == 0xF0
        assert msg.rate == 0x0100


class TestFlooMsgBm:
    def test_create_valid_msg(self):
        msg = FlooMsgBm.create_valid_msg(b"BM=03")
        assert msg is not None
        assert msg.mode == 3

    def test_send_message(self):
        msg = FlooMsgBm(True, 0x05)
        assert b"BC:BM=05" in msg.bytes


class TestFlooMsgPl:
    def test_create_valid_msg(self):
        payload = b"PL=00,001122334455,Test Device"
        msg = FlooMsgPl.create_valid_msg(payload)
        assert msg is not None
        assert msg.index == 0
