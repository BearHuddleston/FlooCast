"""Protocol message classes for FlooGoo communication."""

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
    """FlooGoo BAI message base class."""

    HEADER: str = ""

    def __init__(self, isSend, header, payload=None):
        super().__init__()
        self.isSend = isSend
        self.header = header
        self.bytes = bytearray()
        if isSend:
            self.bytes.extend(b"BC:")
        self.bytes.extend(header.encode("ascii"))
        if payload is not None:
            self.bytes.extend(b"=")
            self.bytes.extend(payload)
        self.bytes.extend(b"\r\n")


class _HexValueMessage(FlooMessage):
    """Base class for messages with a single hex-encoded value."""

    VALUE_ATTR: str = "value"
    STRICT_LENGTH: bool = True
    ENCODING: str = "ascii"

    def __init__(self, isSend, value=None):
        setattr(self, self.VALUE_ATTR, value)
        if value is not None:
            super().__init__(isSend, self.HEADER, b"%02X" % value)
        else:
            super().__init__(isSend, self.HEADER)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        msgLen = len(payload)
        if cls.STRICT_LENGTH and msgLen != 5:
            return None
        if msgLen < 5:
            return None
        return cls(False, int(payload[3:5].decode(cls.ENCODING), 16))


class _SendOnlyCommand(FlooMessage):
    """Base class for send-only commands with no parameters."""

    def __init__(self):
        super().__init__(True, self.HEADER)


class _IndexedCommand(FlooMessage):
    """Base class for commands with optional index parameter."""

    def __init__(self, index=None):
        if index is None:
            super().__init__(True, self.HEADER)
        else:
            super().__init__(True, self.HEADER, b"%02X" % index)


class _StringPayloadMessage(FlooMessage):
    """Base class for messages with string payload."""

    VALUE_ATTR: str = "value"
    MIN_LENGTH: int = 4

    def __init__(self, isSend, value=None):
        setattr(self, self.VALUE_ATTR, value)
        if not isSend or value is None:
            super().__init__(isSend, self.HEADER)
        else:
            super().__init__(isSend, self.HEADER, value.encode("utf-8"))

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) < cls.MIN_LENGTH:
            return None
        return cls(False, payload[3:].decode("utf-8"))


class FlooMsgAc(FlooMessage):
    """Audio Codec in Use - AC=xx with extended fields."""

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
            payload = (
                f"{codec:02X},{rssi:02X},{rate:04X},{spkSampleRate:04X},"
                f"{micSampleRate:04X},{sduInterval:04X},{transportDelay:04X},{presentDelay:04X}"
            )
            super().__init__(isSend, self.HEADER, payload.encode("ascii"))
        else:
            super().__init__(isSend, self.HEADER)

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
    """Address message - AD=addr(U48)."""

    HEADER = "AD"

    def __init__(self, isSend, addr=None, payload=None):
        self.addr = addr
        if isSend:
            super().__init__(isSend, self.HEADER)
        else:
            super().__init__(isSend, self.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) != 15:
            return None
        return cls(False, payload[3:15], payload[3:])


class FlooMsgAm(_HexValueMessage):
    """Audio Mode - AM=xx (Bit 0~1: 00 high quality, 01 gaming, 02 broadcast)."""

    HEADER = "AM"
    VALUE_ATTR = "mode"
    STRICT_LENGTH = False
    ENCODING = "utf-8"


class FlooMsgBe(_StringPayloadMessage):
    """Broadcast Encryption Key - BE=<KEY>."""

    HEADER = "BE"
    VALUE_ATTR = "key"
    MIN_LENGTH = 5

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) != 5:
            return None
        return cls(False, payload[3:].decode("utf-8"))


class FlooMsgBm(_HexValueMessage):
    """Broadcast Mode - BM=xx (encryption, quality, latency bits)."""

    HEADER = "BM"
    VALUE_ATTR = "mode"


class FlooMsgBn(_StringPayloadMessage):
    """Broadcast Name - BN=<name>."""

    HEADER = "BN"
    VALUE_ATTR = "name"


class FlooMsgCp(_IndexedCommand):
    """Connect to Paired device - CP=xx."""

    HEADER = "CP"


class FlooMsgCt(_IndexedCommand):
    """Connect and Trust - CT=xx."""

    HEADER = "CT"


class FlooMsgDc(_SendOnlyCommand):
    """Disconnect - DC."""

    HEADER = "DC"


class FlooMsgEr(FlooMessage):
    """Error message - ER=xx."""

    HEADER = "ER"

    def __init__(self, isSend, error):
        self.error = error
        super().__init__(isSend, self.HEADER, b"%02d" % error)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii")))


class FlooMsgFd(_SendOnlyCommand):
    """Factory Default - FD."""

    HEADER = "FD"


class FlooMsgFn(FlooMessage):
    """Friendly Name - FN=<index>,<addr>,<name>."""

    HEADER = "FN"

    def __init__(self, isSend, index=None, btAddress=None, name=None):
        if isSend:
            self.index = None
            self.name = None
            self.btAddress = None
            super().__init__(isSend, self.HEADER)
        else:
            self.index = index
            self.btAddress = btAddress
            if btAddress is None:
                self.name = None
                paramStr = "%02X" % index
            else:
                self.name = "No Name" if name is None else name
                paramStr = "%02X,%s,%s" % (index, btAddress, self.name)
            super().__init__(isSend, self.HEADER, paramStr.encode("utf-8"))

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
        return None


class FlooMsgFt(_HexValueMessage):
    """Feature bits - FT=xx (LSB: LED ON/OFF)."""

    HEADER = "FT"
    VALUE_ATTR = "feature"
    STRICT_LENGTH = False


class FlooMsgIq(_SendOnlyCommand):
    """Inquiry - IQ."""

    HEADER = "IQ"


class FlooMsgLa(_HexValueMessage):
    """LE Audio state - LA=xx."""

    HEADER = "LA"
    VALUE_ATTR = "state"

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) != 5:
            return None
        return cls(False, int(payload[3:5].decode("ascii")))


class FlooMsgLf(_HexValueMessage):
    """LE Audio preference - LF=xx (00 prefer A2DP, 01 prefer LEA)."""

    HEADER = "LF"
    VALUE_ATTR = "mode"
    STRICT_LENGTH = False
    ENCODING = "utf-8"


class FlooMsgMd(_HexValueMessage):
    """Discoverable Mode - MD=xx."""

    HEADER = "MD"
    VALUE_ATTR = "mode"
    STRICT_LENGTH = False
    ENCODING = "utf-8"


class FlooMsgOk(FlooMessage):
    """OK response message."""

    HEADER = "OK"

    def __init__(self, isSend):
        super().__init__(isSend, self.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes):
        if len(pkt) != 2:
            return None
        return cls(False)


class FlooMsgPl(FlooMessage):
    """Paired device List - PL=index(U8),addr(U48),name(str)."""

    HEADER = "PL"

    def __init__(self, isSend, index=None, addr=None, name=None, payload=None):
        self.index = index
        self.addr = addr
        self.name = name
        if isSend:
            super().__init__(isSend, self.HEADER)
        else:
            super().__init__(isSend, self.HEADER, payload)

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) < 20:
            return None
        return cls(
            False, int(payload[3:5].decode("utf-8")), payload[6:18], payload[19:], payload[3:]
        )


class FlooMsgSt(_HexValueMessage):
    """Source State - ST=xx."""

    HEADER = "ST"
    VALUE_ATTR = "state"


class FlooMsgTc(_IndexedCommand):
    """Terminate Connection - TC=xx."""

    HEADER = "TC"


class FlooMsgUnknown(FlooMessage):
    """Unknown message type."""

    HEADER = "~~"

    def __init__(self, isSend):
        super().__init__(isSend, self.HEADER)

    @classmethod
    def create_valid_msg(cls, pkt: bytes = None):
        return cls(False)


class FlooMsgVr(_StringPayloadMessage):
    """Version - VR=<version string>."""

    HEADER = "VR"
    VALUE_ATTR = "verStr"

    def __init__(self, isSend, version=None):
        self.verStr = version
        if isSend:
            FlooMessage.__init__(self, isSend, self.HEADER)
        else:
            FlooMessage.__init__(
                self, isSend, self.HEADER, version.encode("utf-8") if version else None
            )

    @classmethod
    def create_valid_msg(cls, payload: bytes):
        if len(payload) < 4:
            return None
        return cls(False, payload[3:].decode("utf-8"))
