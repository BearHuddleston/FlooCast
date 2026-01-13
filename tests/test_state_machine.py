from unittest.mock import MagicMock, patch

import pytest

from floocast.protocol.messages import (
    FlooMsgAc,
    FlooMsgAm,
    FlooMsgBm,
    FlooMsgBn,
    FlooMsgEr,
    FlooMsgFn,
    FlooMsgFt,
    FlooMsgLa,
    FlooMsgLf,
    FlooMsgOk,
    FlooMsgSt,
    FlooMsgVr,
)
from floocast.protocol.state_machine import (
    BroadcastModeBit,
    FeatureBit,
    FlooStateMachine,
    SourceState,
)
from floocast.protocol.state_machine_delegate import FlooStateMachineDelegate


def sync_call_after(func, *args):
    func(*args)


@pytest.fixture
def mock_delegate():
    delegate = MagicMock(spec=FlooStateMachineDelegate)
    return delegate


@pytest.fixture
def mock_settings():
    settings = MagicMock()
    settings.get_item.return_value = None
    return settings


@pytest.fixture
def state_machine(mock_delegate, mock_settings):
    with (
        patch("floocast.protocol.state_machine.FlooSettings", return_value=mock_settings),
        patch("floocast.protocol.state_machine.FlooInterface"),
        patch("floocast.protocol.state_machine._wx_call_after", sync_call_after),
    ):
        sm = FlooStateMachine(mock_delegate)
        return sm


class TestStateMachineInit:
    def test_initial_state_is_init(self, state_machine):
        assert state_machine.state == FlooStateMachine.INIT

    def test_delegate_is_set(self, state_machine, mock_delegate):
        assert state_machine.delegate == mock_delegate


class TestInterfaceStateCallback:
    def test_interface_enabled_triggers_version_query(self, state_machine):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.interfaceState(True, "ttyUSB0")
            assert state_machine.lastCmd is not None
            assert state_machine.lastCmd.header == "VR"

    def test_interface_disabled_resets_state(self, state_machine, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.state = FlooStateMachine.CONNECTED
            state_machine.interfaceState(False, None)
            assert state_machine.state == FlooStateMachine.INIT
            mock_delegate.deviceDetected.assert_called_with(False, None)


class TestHandshakeSequence:
    def test_vr_response_triggers_am_query(self, state_machine):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.interfaceState(True, "ttyUSB0")
            vr_msg = FlooMsgVr(False, "1.0.0")
            state_machine.handleMessage(vr_msg)
            assert state_machine.lastCmd.header == "AM"

    def test_am_response_triggers_st_query(self, state_machine):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.interfaceState(True, "ttyUSB0")
            state_machine.handleMessage(FlooMsgVr(False, "1.0.0"))
            state_machine.handleMessage(FlooMsgAm.create_valid_msg(b"AM=02"))
            assert state_machine.lastCmd.header == "ST"
            assert state_machine.audioMode == 2

    def test_st_response_triggers_la_query(self, state_machine):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.interfaceState(True, "ttyUSB0")
            state_machine.handleMessage(FlooMsgVr(False, "1.0.0"))
            state_machine.handleMessage(FlooMsgAm.create_valid_msg(b"AM=00"))
            state_machine.handleMessage(FlooMsgSt.create_valid_msg(b"ST=01"))
            assert state_machine.lastCmd.header == "LA"
            assert state_machine.sourceState == 1

    def test_full_handshake_reaches_connected_state(self, state_machine, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.interfaceState(True, "ttyUSB0")
            state_machine.handleMessage(FlooMsgVr(False, "1.0.0"))
            state_machine.handleMessage(FlooMsgAm.create_valid_msg(b"AM=00"))
            state_machine.handleMessage(FlooMsgSt.create_valid_msg(b"ST=01"))
            state_machine.handleMessage(FlooMsgLa.create_valid_msg(b"LA=00"))
            state_machine.handleMessage(FlooMsgLf.create_valid_msg(b"LF=00"))
            state_machine.handleMessage(FlooMsgBm.create_valid_msg(b"BM=00"))
            state_machine.handleMessage(FlooMsgBn.create_valid_msg(b"BN=Test"))
            state_machine.handleMessage(FlooMsgFn(False, 0))
            state_machine.handleMessage(FlooMsgFt.create_valid_msg(b"FT=01"))
            state_machine.handleMessage(FlooMsgAc.create_valid_msg(b"AC=00"))
            assert state_machine.state == FlooStateMachine.CONNECTED
            mock_delegate.deviceDetected.assert_called()


class TestConnectedStateCommands:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        return state_machine

    def test_set_audio_mode_sends_command(self, connected_sm):
        connected_sm.setAudioMode(1)
        assert connected_sm.lastCmd.header == "AM"

    def test_set_audio_mode_ok_response_updates_state(self, connected_sm):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.setAudioMode(1)
            connected_sm.handleMessage(FlooMsgOk(False))
            assert connected_sm.audioMode == 1

    def test_set_audio_mode_error_response_reverts(self, connected_sm, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.audioMode = 0
            connected_sm.setAudioMode(2)
            connected_sm.handleMessage(FlooMsgEr(False, 1))
            mock_delegate.audioModeInd.assert_called_with(0)

    def test_set_prefer_lea_sends_command(self, connected_sm):
        connected_sm.setPreferLea(True)
        assert connected_sm.lastCmd.header == "LF"

    def test_enable_led_sends_command(self, connected_sm):
        connected_sm.feature = 0
        connected_sm.enableLed(True)
        assert connected_sm.lastCmd.header == "FT"

    def test_enable_led_ok_updates_feature(self, connected_sm, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.feature = 0
            connected_sm.enableLed(True)
            connected_sm.handleMessage(FlooMsgOk(False))
            assert connected_sm.feature & FeatureBit.LED


class TestBroadcastModeCommands:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        state_machine.broadcastMode = 0
        return state_machine

    def test_set_public_broadcast_sets_bit(self, connected_sm):
        connected_sm.setPublicBroadcast(True)
        assert connected_sm.lastCmd.header == "BM"

    def test_set_public_broadcast_ok_updates_mode(self, connected_sm):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.setPublicBroadcast(True)
            connected_sm.handleMessage(FlooMsgOk(False))
            assert connected_sm.broadcastMode & BroadcastModeBit.PUBLIC

    def test_set_broadcast_high_quality(self, connected_sm):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.setBroadcastHighQuality(True)
            connected_sm.handleMessage(FlooMsgOk(False))
            assert connected_sm.broadcastMode & BroadcastModeBit.HIGH_QUALITY

    def test_set_broadcast_encrypt(self, connected_sm):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.setBroadcastEncrypt(True)
            connected_sm.handleMessage(FlooMsgOk(False))
            assert connected_sm.broadcastMode & BroadcastModeBit.ENCRYPT

    def test_set_broadcast_latency(self, connected_sm):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.setBroadcastLatency(2)
            connected_sm.handleMessage(FlooMsgOk(False))
            latency = (
                connected_sm.broadcastMode & BroadcastModeBit.LATENCY_MASK
            ) >> BroadcastModeBit.LATENCY_SHIFT
            assert latency == 2


class TestUnsolicitedMessages:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        return state_machine

    def test_unsolicited_st_updates_source_state(self, connected_sm, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.lastCmd = None
            connected_sm.handleMessage(FlooMsgSt.create_valid_msg(b"ST=04"))
            assert connected_sm.sourceState == 4
            mock_delegate.sourceStateInd.assert_called_with(4)

    def test_unsolicited_la_updates_lea_state(self, connected_sm, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.lastCmd = None
            connected_sm.handleMessage(FlooMsgLa.create_valid_msg(b"LA=02"))
            mock_delegate.leAudioStateInd.assert_called_with(2)

    def test_unsolicited_ac_updates_codec(self, connected_sm, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            connected_sm.lastCmd = None
            connected_sm.handleMessage(FlooMsgAc.create_valid_msg(b"AC=05"))
            mock_delegate.audioCodecInUseInd.assert_called()


class TestAutoReconnect:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        state_machine._sourceStateBeforeDisconnect = SourceState.STREAMING
        state_machine.sourceState = SourceState.IDLE
        return state_machine

    def test_auto_reconnect_triggered_when_was_streaming(self, connected_sm):
        with patch.object(connected_sm, "_scheduleReconnect") as mock_schedule:
            connected_sm._attemptAutoReconnect()
            mock_schedule.assert_called_once()

    def test_no_reconnect_if_already_streaming(self, connected_sm):
        connected_sm.sourceState = SourceState.STREAMING
        with patch.object(connected_sm, "_scheduleReconnect") as mock_schedule:
            connected_sm._attemptAutoReconnect()
            mock_schedule.assert_not_called()

    def test_no_reconnect_if_was_idle(self, connected_sm):
        connected_sm._sourceStateBeforeDisconnect = SourceState.IDLE
        with patch.object(connected_sm, "_scheduleReconnect") as mock_schedule:
            connected_sm._attemptAutoReconnect()
            mock_schedule.assert_not_called()

    def test_max_retries_clears_saved_state(self, connected_sm):
        connected_sm._reconnectAttempts = 8
        with patch.object(connected_sm, "_clearSavedState") as mock_clear:
            connected_sm._scheduleReconnect()
            mock_clear.assert_called_once()


class TestReset:
    def test_reset_clears_state(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        state_machine.sourceState = SourceState.STREAMING
        state_machine.reset()
        assert state_machine.state == FlooStateMachine.INIT


class TestConnectionError:
    def test_connection_error_calls_delegate(self, state_machine, mock_delegate):
        with patch("floocast.protocol.state_machine._wx_call_after", sync_call_after):
            state_machine.connectionError("port_busy")
            mock_delegate.connectionErrorInd.assert_called_with("port_busy")


class TestPairedDevices:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        return state_machine

    def test_toggle_connection_sends_command(self, connected_sm):
        connected_sm.toggleConnection(0)
        assert connected_sm.lastCmd.header in ("CP", "TC")

    def test_clear_all_sends_command(self, connected_sm):
        connected_sm.clearAllPairedDevices()
        assert connected_sm.lastCmd.header == "CP"

    def test_clear_indexed_sends_command(self, connected_sm):
        connected_sm.clearIndexedDevice(1)
        assert connected_sm.lastCmd.header == "CP"


class TestBroadcastSettings:
    @pytest.fixture
    def connected_sm(self, state_machine):
        state_machine.state = FlooStateMachine.CONNECTED
        return state_machine

    def test_set_broadcast_name_sends_command(self, connected_sm):
        connected_sm.setBroadcastName("TestBroadcast")
        assert connected_sm.lastCmd.header == "BN"

    def test_set_broadcast_key_sends_command(self, connected_sm):
        connected_sm.setBroadcastKey("secret")
        assert connected_sm.lastCmd.header == "BE"
