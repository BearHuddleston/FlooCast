__all__ = [
    "FlooMessage",
    "FlooMsgAc",
    "FlooMsgAd",
    "FlooMsgAm",
    "FlooMsgBe",
    "FlooMsgBm",
    "FlooMsgBn",
    "FlooMsgCp",
    "FlooMsgCt",
    "FlooMsgDc",
    "FlooMsgEr",
    "FlooMsgFd",
    "FlooMsgFn",
    "FlooMsgFt",
    "FlooMsgIq",
    "FlooMsgLa",
    "FlooMsgLf",
    "FlooMsgMd",
    "FlooMsgOk",
    "FlooMsgPl",
    "FlooMsgSt",
    "FlooMsgTc",
    "FlooMsgUnknown",
    "FlooMsgVr",
]


class FlooMessage:
    """FlooGoo BAI message"""

    def __init__(self, isSend, header, payload=None):
        super().__init__()
        self.isSend = isSend
        self.header = header
        self.bytes = bytearray()
        if isSend:
            self.bytes.extend(bytes("BC:", "ascii"))
        self.bytes.extend(bytes(header, "ascii"))
        if payload is not None:
            self.bytes.extend(bytes("=", "ascii"))
            self.bytes.extend(payload)
        self.bytes.extend(bytes("\r\n", "ascii"))


class FlooMsgAc(FlooMessage):
    """Audio Codec in Use
    AC=xx
    xx: 01 Voice CVSD
        02 Voice mSBC
        03 A2DP SBC
        04 A2DP APTX
        05 A2DP APTX HD
        06 A2DP APTX Adaptive
        07 LEA LC3
        08 LEA APTX Adaptive
        09 LEA APTX Lite
        0A A2DP APTX Adaptive Lossless
    """

    HEADER = "AC"

    def __init__(
        self,
        isSend,
        codec=None,
        rssi=0,
        rate=0,
        spkSampleRate=0,
        micSampleRate=0,
        sduInterval=0,
        transportDelay=0,
        presentDelay=0,
    ):
        self.codec = codec
        self.rssi = rssi
        self.rate = rate
        self.spkSampleRate = spkSampleRate * 10
        self.micSampleRate = micSampleRate * 10
        self.sduInterval = sduInterval
        self.transportDelay = transportDelay
        self.presentDelay = presentDelay
        if codec is not None:
            adaptiveStr = (
                "%02X" % codec
                + ","
                + "%02X" % rssi
                + ","
                + "%04X" % rate
                + ","
                + "%04X" % spkSampleRate
                + ","
                + "%04X" % micSampleRate
                + ","
                + "%04X" % sduInterval
                + ","
                + "%04X" % transportDelay
                + ","
                + "%04X" % self.presentDelay
            )
            super().__init__(isSend, FlooMsgAc.HEADER, bytes(adaptiveStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgAc.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen == 5:
            return cls(False, int(payload[3:5].decode("ascii"), 16))
        elif msgLen == 13:
            return cls(
                False,
                int(payload[3:5].decode("ascii"), 16),
                int(payload[6:8].decode("ascii"), 16),
                int(payload[9:13].decode("ascii"), 16),
            )
        elif msgLen == 18:
            return cls(
                False,
                int(payload[3:5].decode("ascii"), 16),
                int(payload[6:8].decode("ascii"), 16),
                int(payload[9:13].decode("ascii"), 16),
                int(payload[14:18].decode("ascii"), 16),
            )
        elif msgLen == 23:
            return cls(
                False,
                int(payload[3:5].decode("ascii"), 16),
                int(payload[6:8].decode("ascii"), 16),
                int(payload[9:13].decode("ascii"), 16),
                int(payload[14:18].decode("ascii"), 16),
                int(payload[19:23].decode("ascii"), 16),
            )
        elif msgLen == 38:
            return cls(
                False,
                int(payload[3:5].decode("ascii"), 16),
                int(payload[6:8].decode("ascii"), 16),
                int(payload[9:13].decode("ascii"), 16),
                int(payload[14:18].decode("ascii"), 16),
                int(payload[19:23].decode("ascii"), 16),
                int(payload[24:28].decode("ascii"), 16),
                int(payload[29:33].decode("ascii"), 16),
                int(payload[34:38].decode("ascii"), 16),
            )

        else:
            return cls(False, int(payload[3:5].decode("ascii"), 16))


class FlooMsgAd(FlooMessage):
    """
    BC:AD
    AD=addr(U48)
    """

    HEADER = "AD"

    def __init__(self, isSend, addr=None, payload=None):
        self.addr = addr
        if isSend:
            super().__init__(isSend, FlooMsgAd.HEADER)
        else:
            super().__init__(isSend, FlooMsgAd.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 15:
            return None
        return cls(False, payload[3:15], payload[3:])


class FlooMsgAm(FlooMessage):
    """
    BC:AM
    BC:AM=xx xx:
             Bit 0~1:
             00 high quality, 01 gaming, 02 broadcast
    AM=xx
             Bit 7:
             0: hardware variant FMA120
             1: hardware variant FMA121
    """

    HEADER = "AM"

    def __init__(self, isSend, mode=None):
        self.mode = mode
        if mode is not None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgAm.HEADER, bytes(modStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgAm.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode("utf-8"), 16))


class FlooMsgBe(FlooMessage):
    """
    BC:BE=<KEY> : key of length <=16
    BN=00 or 01 : 00 key has not been set, 01 key set.
    """

    HEADER = "BE"

    def __init__(self, isSend, key=None):
        self.key = key
        if not isSend or key is None:
            super().__init__(isSend, FlooMsgBe.HEADER)
        else:
            super().__init__(isSend, FlooMsgBe.HEADER, bytes(key, "utf-8"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, payload[3:].decode("utf-8"))


class FlooMsgBm(FlooMessage):
    """
    BC:BM
    BC:BM=xx xx:Bit 0~1:
                0 TMAP broadcast, no encrypt
                1 TMAP broadcast, encrypted
                2 PBP broadcast, no encrypt
                3 PBP broadcast, encrypted
                Bit 2:
                0 Broadcast in standard quality
                1 Broadcast in high quality
                Bit 3:
                0 Maintain broadcast for 3 minutes after USB audio playback ends
                1 Stop broadcasting immediately when USB audio playback ends
                Bit 4~5:
                0 reserved
                1 lowest latency
                2 lower latency
                3 default
    BM=xx
    """

    HEADER = "BM"

    def __init__(self, isSend, mode=None):
        self.mode = mode
        if mode is not None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgBm.HEADER, bytes(modStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgBm.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii"), 16))


class FlooMsgBn(FlooMessage):
    """
    BC:BN
    BN=<name>
    """

    HEADER = "BN"

    def __init__(self, isSend, name=None):
        self.name = name
        if not isSend or name is None:
            super().__init__(isSend, FlooMsgBn.HEADER)
        else:
            super().__init__(isSend, FlooMsgBn.HEADER, bytes(name, "utf-8"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 4:
            return None
        return cls(False, payload[3:].decode("utf-8"))


class FlooMsgCp(FlooMessage):
    """
    BC:CP
    BC:CP=xx xx:index of the device
    The module replies OK or ER for CP command
    """

    HEADER = "CP"

    def __init__(self, index=None):
        if index is None:
            super().__init__(True, FlooMsgCp.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgCp.HEADER, bytes(paramStr, "ascii"))


class FlooMsgCt(FlooMessage):
    """
    BC:CT
    BC:CP=xx xx:index of the device
    The module replies OK or ER
    """

    HEADER = "CT"

    def __init__(self, index=None):
        if index is None:
            super().__init__(True, FlooMsgCt.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgCt.HEADER, bytes(paramStr, "ascii"))


class FlooMsgDc(FlooMessage):
    """
    BC:DC
    The module replies OK or ER for CP command
    """

    HEADER = "DC"

    def __init__(self):
        super().__init__(True, FlooMsgDc.HEADER)


class FlooMsgEr(FlooMessage):
    """Error message
    ER=xx
    xx: 01 Last command not allowed in current state
        02 Format error in the last command
    """

    HEADER = "ER"

    def __init__(self, isSend, error):
        self.error = error
        errStr = "%02d" % error
        super().__init__(isSend, FlooMsgEr.HEADER, bytes(errStr, "ascii"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii")))


class FlooMsgFd(FlooMessage):
    """
    BC:FD
    The module replies OK for CP command
    """

    HEADER = "FD"

    def __init__(self):
        super().__init__(True, FlooMsgFd.HEADER)


class FlooMsgFn(FlooMessage):
    """
    BC:FN
    FN=<index>,<name>
    """

    HEADER = "FN"

    def __init__(self, isSend, index=None, btAddress=None, name=None):
        if isSend:
            self.index = None
            self.name = None
            self.btAddress = None
            super().__init__(isSend, FlooMsgFn.HEADER)
        else:
            self.index = index
            self.btAddress = btAddress
            if btAddress is None:
                self.name = None
                paramStr = "%02X" % index
            else:
                self.name = "No Name" if name is None else name
                paramStr = "%02X,%s,%s" % (index, btAddress, self.name)
            super().__init__(isSend, FlooMsgFn.HEADER, bytes(paramStr, "utf-8"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen == 5:
            return cls(False, int(payload[3:5].decode("ascii")))
        elif msgLen == 18:
            return cls(False, int(payload[3:5].decode("ascii")), payload[6:].decode("utf-8"))
        elif msgLen > 19:
            return cls(
                False,
                int(payload[3:5].decode("ascii")),
                payload[6:18].decode("utf-8"),
                payload[19:].decode("utf-8", errors="ignore"),
            )
        else:
            return None


class FlooMsgFt(FlooMessage):
    """
    BC:FT
    BC:FT=xx xx: feature bits, LSB: LED ON/OFF
    FT=xx
    """

    HEADER = "FT"

    def __init__(self, isSend, feature=None):
        self.feature = feature
        if feature is not None:
            featureStr = "%02X" % feature
            super().__init__(isSend, FlooMsgFt.HEADER, bytes(featureStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgFt.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii"), 16))


class FlooMsgIq(FlooMessage):
    """
    BC:IQ
    """

    HEADER = "IQ"

    def __init__(self):
        super().__init__(True, FlooMsgIq.HEADER)


class FlooMsgLa(FlooMessage):
    """
    BC:LA
    LA=xx
    xx: 00 disconnected
        01 connected
        02 unicast streaming starting
        03 unicast streaming
        04 broadcast streaming starting,
        05 broadcast streaming
        06 streaming stopping
    """

    HEADER = "LA"

    def __init__(self, isSend, state=None):
        self.state = state
        if state is not None:
            stateStr = "%02X" % state
            super().__init__(isSend, FlooMsgLa.HEADER, bytes(stateStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgLa.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii")))


class FlooMsgLf(FlooMessage):
    """
    BC:LF
    BC:LF=xx xx:00 prefer A2DP, 01 prefer LEA
    LF=xx
    """

    HEADER = "LF"

    def __init__(self, isSend, mode=None):
        self.mode = mode
        if mode is not None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgLf.HEADER, bytes(modStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgLf.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode("utf-8")))


class FlooMsgMd(FlooMessage):
    """
    BC:MD
    BC:MD=xx xx:00 discoverable off, 01 discoverable on
    MD=xx
    """

    HEADER = "MD"

    def __init__(self, isSend, mode=None):
        self.mode = mode
        if mode is not None:
            modStr = "%02X" % mode
            super().__init__(isSend, FlooMsgMd.HEADER, bytes(modStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgMd.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode("utf-8")))


class FlooMsgOk(FlooMessage):
    """OK message format: OK"""

    HEADER = "OK"

    def __init__(self, isSend):
        super().__init__(isSend, FlooMsgOk.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes):
        msgLen = len(pkt)
        if msgLen != 2:
            print("OK msg create failed")
            return None
        return cls(False)


class FlooMsgPl(FlooMessage):
    """
    BC:PL
    PL=index(U8),addr(U48),name(str)
    """

    HEADER = "PL"

    def __init__(self, isSend, index=None, addr=None, name=None, payload=None):
        self.index = index
        self.addr = addr
        self.name = name
        if isSend:
            super().__init__(isSend, FlooMsgPl.HEADER)
        else:
            super().__init__(isSend, FlooMsgPl.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 20:
            return None
        return cls(
            False, int(payload[3:5].decode("utf-8")), payload[6:18], payload[19:], payload[3:]
        )


class FlooMsgSt(FlooMessage):
    """
    BC:ST
    ST=xx
    xx: 00 Init
        01 Idle
        02 Pairing
        03 Connecting
        04 Connected
        05 Audio starting
        06 Audio streaming
        07 Audio stopping
        08 Disconnecting
        09 Voice staring
        0A Voice streaming
        0B Voice stopping
    """

    HEADER = "ST"

    def __init__(self, isSend, state=None):
        self.state = state
        if state is not None:
            stateStr = "%02X" % state
            super().__init__(isSend, FlooMsgSt.HEADER, bytes(stateStr, "ascii"))
        else:
            super().__init__(isSend, FlooMsgSt.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii"), 16))


class FlooMsgTc(FlooMessage):
    """
    BC:TC
    BC:TC=xx xx:index of the device
    The module replies OK or ER for TC command
    """

    HEADER = "TC"

    def __init__(self, index=None):
        if index is None:
            super().__init__(True, FlooMsgTc.HEADER)
        else:
            paramStr = "%02X" % index
            super().__init__(True, FlooMsgTc.HEADER, bytes(paramStr, "ascii"))


class FlooMsgUnknown(FlooMessage):
    """Unknown message"""

    HEADER = "~~"

    def __init__(self, isSend):
        super().__init__(isSend, FlooMsgUnknown.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes = None):
        return cls(False)


class FlooMsgVr(FlooMessage):
    """
    BC:VR
    VR=version string, such as 1.0.0.0
    """

    HEADER = "VR"

    def __init__(self, isSend, version=None):
        self.verStr = version
        if isSend:
            super().__init__(isSend, FlooMsgVr.HEADER)
        else:
            super().__init__(isSend, FlooMsgVr.HEADER, bytes(version, "utf-8"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if msgLen < 4:
            return None
        return cls(False, payload[3:].decode("utf-8"))
