import logging
from threading import RLock, Thread

from floocast.protocol.interface import FlooInterface
from floocast.protocol.interface_delegate import FlooInterfaceDelegate
from floocast.protocol.messages import (
    FlooMessage,
    FlooMsgAc,
    FlooMsgAm,
    FlooMsgBe,
    FlooMsgBm,
    FlooMsgBn,
    FlooMsgCp,
    FlooMsgEr,
    FlooMsgFn,
    FlooMsgFt,
    FlooMsgIq,
    FlooMsgLa,
    FlooMsgLf,
    FlooMsgMd,
    FlooMsgOk,
    FlooMsgSt,
    FlooMsgTc,
    FlooMsgVr,
)
from floocast.settings import FlooSettings

logger = logging.getLogger(__name__)


class SourceState:
    """Source state constants."""

    IDLE = 1
    STREAMING_START = 4
    STREAMING = 6


class FeatureBit:
    """Feature flag bit masks."""

    LED = 0x01
    APTX_LOSSLESS = 0x02
    GATT_CLIENT = 0x04
    AUDIO_SOURCE = 0x08


class BroadcastModeBit:
    """Broadcast mode bit masks."""

    ENCRYPT = 0x01
    PUBLIC = 0x02
    HIGH_QUALITY = 0x04
    STOP_ON_IDLE = 0x08
    LATENCY_MASK = 0x30
    LATENCY_SHIFT = 4
    FLAGS_MASK = 0x0F
    ALL_MASK = 0x3F


def _wx_call_after(func, *args):
    import wx

    wx.CallAfter(func, *args)


def _wx_call_later(delay_ms, func):
    import wx

    return wx.CallLater(delay_ms, func)


class FlooStateMachine(FlooInterfaceDelegate, Thread):
    """The state machine of the host app working with FlooGoo USB Bluetooth Dongle"""

    INIT = -1
    CONNECTED = 0

    def __init__(self, delegate):
        super().__init__()
        self._lock = RLock()
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.delegate = delegate
        self.inf = FlooInterface(self)
        self.pendingCmdPara = None
        self.audioMode = None
        self.preferLea = None
        self.broadcastMode = None
        self.broadcastName = None
        self.broadcastKey = None
        self.pairedDevices = []
        self.sourceState = None
        self.a2dpSink = False
        self.feature = None
        self._sourceStateBeforeDisconnect = None
        self._reconnectAttempts = 0
        self._reconnectTimer = None
        self._settings = FlooSettings()
        self._lastSavedState = None
        saved_state = self._settings.get_item("last_streaming_state")
        if saved_state is not None and saved_state >= SourceState.STREAMING_START:
            logger.info("Restored last streaming state: %s", saved_state)
            self._sourceStateBeforeDisconnect = saved_state
            self._clearSavedState()

    def reset(self):
        self.state = FlooStateMachine.INIT
        self.lastCmd = None
        self.pendingCmdPara = None
        self.a2dpSink = False
        self.feature = None

    def run(self):
        self.inf.run()

    def interfaceState(self, enabled: bool, port: str):
        if enabled and self.state == FlooStateMachine.INIT:
            cmdReadVersion = FlooMsgVr(True)
            self.inf.sendMsg(cmdReadVersion)
            self.lastCmd = cmdReadVersion
        elif not enabled:
            logger.info("Device disconnected, saving sourceState=%s", self.sourceState)
            self._sourceStateBeforeDisconnect = self.sourceState
            self.lastCmd = None
            self.pendingCmdPara = None
            self.state = FlooStateMachine.INIT
            _wx_call_after(self.delegate.deviceDetected, False, None)

    def connectionError(self, error: str):
        _wx_call_after(self.delegate.connectionErrorInd, error)

    def handleMessage(self, message: FlooMessage):
        logger.debug("handleMessage %s", message.header)
        if self.state == FlooStateMachine.INIT:
            if isinstance(message, FlooMsgVr):
                if isinstance(self.lastCmd, FlooMsgVr):
                    if message.verStr.startswith("AS"):
                        self.a2dpSink = True
                    else:
                        self.a2dpSink = False
                    _wx_call_after(
                        self.delegate.deviceDetected, True, self.inf.port_name, message.verStr
                    )
                    cmdGetAudioMode = FlooMsgAm(True)
                    self.inf.sendMsg(cmdGetAudioMode)
                    self.lastCmd = cmdGetAudioMode
            elif isinstance(message, FlooMsgAm):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.audioMode = message.mode
                    _wx_call_after(self.delegate.audioModeInd, message.mode)
                    cmdGetSourceState = FlooMsgSt(True)
                    self.inf.sendMsg(cmdGetSourceState)
                    self.lastCmd = cmdGetSourceState
            elif isinstance(message, FlooMsgSt):
                logger.debug("ST message: state=%s", message.state)
                self.sourceState = message.state
                _wx_call_after(self.delegate.sourceStateInd, message.state)
                if isinstance(self.lastCmd, FlooMsgSt):
                    cmdGetLeaState = FlooMsgLa(True)
                    self.inf.sendMsg(cmdGetLeaState)
                    self.lastCmd = cmdGetLeaState
            elif isinstance(message, FlooMsgLa):
                if isinstance(self.lastCmd, FlooMsgLa):
                    _wx_call_after(self.delegate.leAudioStateInd, message.state)
                    cmdGetPreferLea = FlooMsgLf(True)
                    self.inf.sendMsg(cmdGetPreferLea)
                    self.lastCmd = cmdGetPreferLea
            elif isinstance(message, FlooMsgLf):
                if isinstance(self.lastCmd, FlooMsgLf):
                    _wx_call_after(self.delegate.preferLeaInd, message.mode)
                    cmdGetBroadcastMode = FlooMsgBm(True)
                    self.inf.sendMsg(cmdGetBroadcastMode)
                    self.lastCmd = cmdGetBroadcastMode
            elif isinstance(message, FlooMsgBm):
                if isinstance(self.lastCmd, FlooMsgBm):
                    self.broadcastMode = message.mode
                    _wx_call_after(self.delegate.broadcastModeInd, message.mode)
                    cmdGetBroadcastName = FlooMsgBn(True)
                    self.inf.sendMsg(cmdGetBroadcastName)
                    self.lastCmd = cmdGetBroadcastName
            elif isinstance(message, FlooMsgBn):
                if isinstance(self.lastCmd, FlooMsgBn):
                    self.broadcastName = message.name
                    _wx_call_after(self.delegate.broadcastNameInd, message.name)
                    self.pairedDevices.clear()
                    cmdGetDeviceName = FlooMsgFn(True)
                    self.inf.sendMsg(cmdGetDeviceName)
                    self.lastCmd = cmdGetDeviceName
            elif isinstance(message, FlooMsgFn):
                if isinstance(self.lastCmd, FlooMsgFn):
                    if message.btAddress is None:
                        # end of the device list
                        _wx_call_after(self.delegate.pairedDevicesUpdateInd, self.pairedDevices)
                        cmdGetFeature = FlooMsgFt(True)
                        self.inf.sendMsg(cmdGetFeature)
                        self.lastCmd = cmdGetFeature
                    else:
                        self.pairedDevices.append(message.name)
            elif isinstance(message, FlooMsgFt):
                if isinstance(self.lastCmd, FlooMsgFt) and message.feature is not None:
                    self.feature = message.feature
                    _wx_call_after(self.delegate.ledEnabledInd, message.feature & FeatureBit.LED)
                    _wx_call_after(
                        self.delegate.aptxLosslessEnabledInd,
                        1
                        if (message.feature & FeatureBit.APTX_LOSSLESS) == FeatureBit.APTX_LOSSLESS
                        else 0,
                    )
                    _wx_call_after(
                        self.delegate.gattClientEnabledInd,
                        1
                        if (self.feature & FeatureBit.GATT_CLIENT) == FeatureBit.GATT_CLIENT
                        else 0,
                    )
                    _wx_call_after(
                        self.delegate.audioSourceInd,
                        1
                        if (self.feature & FeatureBit.AUDIO_SOURCE) == FeatureBit.AUDIO_SOURCE
                        else 0,
                    )
                    cmdGetCodecInUse = FlooMsgAc(True)
                    self.inf.sendMsg(cmdGetCodecInUse)
                    self.lastCmd = cmdGetCodecInUse
            elif isinstance(message, FlooMsgAc | FlooMsgEr):
                if isinstance(self.lastCmd, FlooMsgAc) and isinstance(message, FlooMsgAc):
                    _wx_call_after(
                        self.delegate.audioCodecInUseInd,
                        message.codec,
                        message.rssi,
                        message.rate,
                        message.spkSampleRate,
                        message.micSampleRate,
                        message.sduInterval,
                        message.transportDelay,
                        message.presentDelay,
                    )
                    self.lastCmd = None
                    self.state = FlooStateMachine.CONNECTED
                    self._attemptAutoReconnect()

        elif self.state == FlooStateMachine.CONNECTED:
            if isinstance(message, FlooMsgOk):
                if isinstance(self.lastCmd, FlooMsgAm):
                    self.audioMode = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgLf):
                    self.preferLea = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBm):
                    self.broadcastMode = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBn):
                    self.broadcastName = self.pendingCmdPara
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgBe):
                    self.lastCmd = None
                elif isinstance(self.lastCmd, FlooMsgCp):
                    self.pairedDevices.clear()
                    self.delegate.pairedDevicesUpdateInd([])
                elif isinstance(self.lastCmd, FlooMsgFt):
                    self.feature = self.lastCmd.feature
                    self.lastCmd = None
                else:
                    self.lastCmd = None
                self.pendingCmdPara = None
            elif isinstance(message, FlooMsgEr):
                if isinstance(self.lastCmd, FlooMsgAm):
                    _wx_call_after(self.delegate.audioModeInd, self.audioMode)
                elif isinstance(self.lastCmd, FlooMsgLf):
                    _wx_call_after(self.delegate.preferLeaInd, self.preferLea)
                elif isinstance(self.lastCmd, FlooMsgBm):
                    _wx_call_after(self.delegate.broadcastModeInd, self.broadcastMode)
                elif isinstance(self.lastCmd, FlooMsgBn):
                    _wx_call_after(self.delegate.broadcastNameInd, self.broadcastName)
                elif isinstance(self.lastCmd, FlooMsgFt):
                    _wx_call_after(self.delegate.ledEnabledInd, self.feature & FeatureBit.LED)
                    _wx_call_after(
                        self.delegate.aptxLosslessEnabledInd,
                        1
                        if (self.feature & FeatureBit.APTX_LOSSLESS) == FeatureBit.APTX_LOSSLESS
                        else 0,
                    )
                    _wx_call_after(
                        self.delegate.gattClientEnabledInd,
                        1
                        if (self.feature & FeatureBit.GATT_CLIENT) == FeatureBit.GATT_CLIENT
                        else 0,
                    )
                self.lastCmd = None
                self.pendingCmdPara = None
            elif isinstance(message, FlooMsgSt):
                logger.debug("ST message (CONNECTED): state=%s", message.state)
                self.sourceState = message.state
                _wx_call_after(self.delegate.sourceStateInd, message.state)
                if (
                    message.state is not None
                    and message.state >= SourceState.STREAMING_START
                    and message.state != self._lastSavedState
                ):
                    self._lastSavedState = message.state
                    self._settings.set_item("last_streaming_state", message.state)
                    self._settings.save()
                if message.state in (SourceState.STREAMING_START, SourceState.STREAMING):
                    self.getRecentlyUsedDevices()
            elif isinstance(message, FlooMsgLa):
                _wx_call_after(self.delegate.leAudioStateInd, message.state)
            elif isinstance(message, FlooMsgFn):
                if message.btAddress is None:
                    # end of the device list
                    _wx_call_after(self.delegate.pairedDevicesUpdateInd, self.pairedDevices)
                    self.lastCmd = None
                else:
                    self.pairedDevices.append(message.name)
            elif isinstance(message, FlooMsgAc):
                _wx_call_after(
                    self.delegate.audioCodecInUseInd,
                    message.codec,
                    message.rssi,
                    message.rate,
                    message.spkSampleRate,
                    message.micSampleRate,
                    message.sduInterval,
                    message.transportDelay,
                    message.presentDelay,
                )
            elif isinstance(message, FlooMsgFt) and message.feature is not None:
                self.feature = message.feature
                _wx_call_after(self.delegate.ledEnabledInd, self.feature & FeatureBit.LED)
                _wx_call_after(
                    self.delegate.aptxLosslessEnabledInd,
                    1
                    if (self.feature & FeatureBit.APTX_LOSSLESS) == FeatureBit.APTX_LOSSLESS
                    else 0,
                )
                _wx_call_after(
                    self.delegate.gattClientEnabledInd,
                    1 if (self.feature & FeatureBit.GATT_CLIENT) == FeatureBit.GATT_CLIENT else 0,
                )

    def setAudioMode(self, mode: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdSetAudioMode = FlooMsgAm(True, mode)
                self.pendingCmdPara = mode
                self.lastCmd = cmdSetAudioMode
                self.inf.sendMsg(cmdSetAudioMode)

    def setPreferLea(self, enable: bool):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdPreferLea = FlooMsgLf(True, 1 if enable else 0)
                self.pendingCmdPara = enable
                self.lastCmd = cmdPreferLea
                self.inf.sendMsg(cmdPreferLea)

    def setPublicBroadcast(self, enable: bool):
        with self._lock:
            bit = BroadcastModeBit.PUBLIC
            oldValue = self.broadcastMode & bit != 0
            if oldValue != enable:
                logger.debug("setPublicBroadcast")
                self.pendingCmdPara = (self.broadcastMode & ~bit & BroadcastModeBit.ALL_MASK) | (
                    bit if enable else 0
                )
                cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
                self.lastCmd = cmdSetBroadcastMode
                self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastHighQuality(self, enable: bool):
        with self._lock:
            bit = BroadcastModeBit.HIGH_QUALITY
            oldValue = self.broadcastMode & bit != 0
            if oldValue != enable:
                logger.debug("setBroadcastHighQuality")
                self.pendingCmdPara = (self.broadcastMode & ~bit & BroadcastModeBit.ALL_MASK) | (
                    bit if enable else 0
                )
                cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
                self.lastCmd = cmdSetBroadcastMode
                self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastEncrypt(self, enable: bool):
        with self._lock:
            bit = BroadcastModeBit.ENCRYPT
            oldValue = self.broadcastMode & bit != 0
            if oldValue != enable:
                logger.debug("setBroadcastEncrypt old: %d, new %d", oldValue, enable)
                self.pendingCmdPara = (self.broadcastMode & ~bit & BroadcastModeBit.ALL_MASK) | (
                    bit if enable else 0
                )
                cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
                self.lastCmd = cmdSetBroadcastMode
                self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastStopOnIdle(self, enable: bool):
        with self._lock:
            bit = BroadcastModeBit.STOP_ON_IDLE
            oldValue = self.broadcastMode & bit != 0
            if oldValue != enable:
                logger.debug("setBroadcastStopOnIdle old: %d, new %d", oldValue, enable)
                self.pendingCmdPara = (self.broadcastMode & ~bit & BroadcastModeBit.ALL_MASK) | (
                    bit if enable else 0
                )
                cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
                self.lastCmd = cmdSetBroadcastMode
                self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastLatency(self, mode: int):
        with self._lock:
            oldValue = (
                self.broadcastMode & BroadcastModeBit.LATENCY_MASK
            ) >> BroadcastModeBit.LATENCY_SHIFT
            if oldValue != mode:
                logger.debug("setBroadcastLatency old: %d, new %d", oldValue, mode)
                self.pendingCmdPara = (self.broadcastMode & BroadcastModeBit.FLAGS_MASK) | (
                    mode << BroadcastModeBit.LATENCY_SHIFT
                )
                cmdSetBroadcastMode = FlooMsgBm(True, self.pendingCmdPara)
                self.lastCmd = cmdSetBroadcastMode
                self.inf.sendMsg(cmdSetBroadcastMode)

    def setBroadcastName(self, name: str):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdSetBroadcastName = FlooMsgBn(True, name)
                self.pendingCmdPara = name
                self.lastCmd = cmdSetBroadcastName
                self.inf.sendMsg(cmdSetBroadcastName)

    def setBroadcastKey(self, key: str):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdSetBroadcastKey = FlooMsgBe(True, key)
                self.pendingCmdPara = key
                self.lastCmd = cmdSetBroadcastKey
                self.inf.sendMsg(cmdSetBroadcastKey)

    def setNewPairing(self):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                if self.a2dpSink:
                    cmdSetDiscoverable = FlooMsgMd(True, 1)
                    self.pendingCmdPara = 1
                    self.lastCmd = cmdSetDiscoverable
                    self.inf.sendMsg(cmdSetDiscoverable)
                else:
                    cmdStartNewPairing = FlooMsgIq()
                    self.lastCmd = cmdStartNewPairing
                    self.inf.sendMsg(cmdStartNewPairing)

    def clearAllPairedDevices(self):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdClearAllPairedDevices = FlooMsgCp()
                self.lastCmd = cmdClearAllPairedDevices
                self.inf.sendMsg(cmdClearAllPairedDevices)

    def clearIndexedDevice(self, index: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdClearIndexedDevice = FlooMsgCp(index)
                self.lastCmd = cmdClearIndexedDevice
                self.inf.sendMsg(cmdClearIndexedDevice)

    def _attemptAutoReconnect(self):
        prevState = self._sourceStateBeforeDisconnect
        currState = self.sourceState
        logger.debug("_attemptAutoReconnect: prevState=%s, currState=%s", prevState, currState)
        if (
            prevState is not None
            and prevState >= SourceState.STREAMING_START
            and currState == SourceState.IDLE
        ):
            self._reconnectAttempts = 0
            self._scheduleReconnect()
        else:
            logger.debug("Auto-reconnect skipped: conditions not met")
        self._sourceStateBeforeDisconnect = None

    def _clearSavedState(self):
        self._lastSavedState = None
        self._settings.set_item("last_streaming_state", None)
        self._settings.save()

    def _cancelReconnectTimer(self):
        if self._reconnectTimer is not None:
            try:
                self._reconnectTimer.Stop()
            except RuntimeError:
                pass
            self._reconnectTimer = None

    def _scheduleReconnect(self):
        MAX_RETRIES = 8
        RETRY_DELAYS = [2000, 3000, 4000, 5000, 6000, 8000, 10000, 15000]
        if self._reconnectAttempts >= MAX_RETRIES:
            logger.info("Auto-reconnect: gave up after %d attempts", MAX_RETRIES)
            self._clearSavedState()
            return
        if self.sourceState >= SourceState.STREAMING_START:
            logger.debug("Auto-reconnect: already connected (state=%s)", self.sourceState)
            return
        self._cancelReconnectTimer()
        delay = RETRY_DELAYS[min(self._reconnectAttempts, len(RETRY_DELAYS) - 1)]
        logger.debug(
            "Auto-reconnect: scheduling attempt %d in %dms", self._reconnectAttempts + 1, delay
        )
        _wx_call_after(
            lambda: setattr(self, "_reconnectTimer", _wx_call_later(delay, self._doReconnect))
        )

    def _doReconnect(self):
        self._reconnectAttempts += 1
        if self.sourceState >= SourceState.STREAMING_START:
            logger.debug("Auto-reconnect: already connected, cancelling")
            return
        if self.sourceState != 1:
            logger.debug("Auto-reconnect: state=%s, retrying later", self.sourceState)
            self._scheduleReconnect()
            return
        logger.debug("Auto-reconnect: attempt %d, toggling device 0", self._reconnectAttempts)
        self.toggleConnection(0)
        _wx_call_after(lambda: _wx_call_later(3000, self._checkReconnectResult))

    def _checkReconnectResult(self):
        if self.sourceState >= SourceState.STREAMING_START:
            logger.info("Auto-reconnect: success! state=%s", self.sourceState)
            self._reconnectAttempts = 0
        elif self.sourceState == 1:
            logger.debug("Auto-reconnect: still idle, scheduling retry")
            self._scheduleReconnect()

    def getRecentlyUsedDevices(self):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                self.pairedDevices.clear()
                cmdGetDeviceName = FlooMsgFn(True)
                self.lastCmd = cmdGetDeviceName
                self.inf.sendMsg(cmdGetDeviceName)

    def toggleConnection(self, index: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                cmdToggleConnection = FlooMsgTc(index)
                self.lastCmd = cmdToggleConnection
                self.inf.sendMsg(cmdToggleConnection)

    def enableLed(self, onOff: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                feature = (self.feature & 0x0E) + onOff
                cmdLedOnOff = FlooMsgFt(True, feature)
                self.pendingCmdPara = feature
                self.lastCmd = cmdLedOnOff
                self.inf.sendMsg(cmdLedOnOff)

    def enableAptxLossless(self, onOff: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                feature = (self.feature & 0x0D) + (0x02 if onOff else 0x00)
                cmdLosslessOnOff = FlooMsgFt(True, feature)
                self.lastCmd = cmdLosslessOnOff
                self.inf.sendMsg(cmdLosslessOnOff)

    def enableGattClient(self, onOff: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                feature = (self.feature & 0x0B) + (0x04 if onOff else 0x00)
                cmdGattClientOnOff = FlooMsgFt(True, feature)
                self.lastCmd = cmdGattClientOnOff
                self.inf.sendMsg(cmdGattClientOnOff)

    def enableUsbInput(self, onOff: int):
        with self._lock:
            if self.state == FlooStateMachine.CONNECTED:
                feature = (self.feature & 0x07) + (0x08 if onOff else 0x00)
                cmdLedOnOff = FlooMsgFt(True, feature)
                self.pendingCmdPara = feature
                self.lastCmd = cmdLedOnOff
                self.inf.sendMsg(cmdLedOnOff)
