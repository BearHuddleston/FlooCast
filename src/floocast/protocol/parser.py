import logging

from floocast.protocol.messages import (
    FlooMessage,
    FlooMsgAc,
    FlooMsgAd,
    FlooMsgAm,
    FlooMsgBm,
    FlooMsgBn,
    FlooMsgEr,
    FlooMsgFn,
    FlooMsgFt,
    FlooMsgLa,
    FlooMsgLf,
    FlooMsgOk,
    FlooMsgPl,
    FlooMsgSt,
    FlooMsgUnknown,
    FlooMsgVr,
)

logger = logging.getLogger(__name__)


class FlooParser:
    """FlooGoo message parser"""

    MSG_HEADERS = {
        FlooMsgOk.HEADER: FlooMsgOk.create_valid_msg,
        FlooMsgPl.HEADER: FlooMsgPl.create_valid_msg,
        FlooMsgAd.HEADER: FlooMsgAd.create_valid_msg,
        FlooMsgAm.HEADER: FlooMsgAm.create_valid_msg,
        FlooMsgLa.HEADER: FlooMsgLa.create_valid_msg,
        FlooMsgSt.HEADER: FlooMsgSt.create_valid_msg,
        FlooMsgBm.HEADER: FlooMsgBm.create_valid_msg,
        FlooMsgBn.HEADER: FlooMsgBn.create_valid_msg,
        FlooMsgFn.HEADER: FlooMsgFn.create_valid_msg,
        FlooMsgEr.HEADER: FlooMsgEr.create_valid_msg,
        FlooMsgAc.HEADER: FlooMsgAc.create_valid_msg,
        FlooMsgLf.HEADER: FlooMsgLf.create_valid_msg,
        FlooMsgVr.HEADER: FlooMsgVr.create_valid_msg,
        FlooMsgFt.HEADER: FlooMsgFt.create_valid_msg,
    }

    def __init__(self):
        super().__init__()

    def create_valid_message(self, pkt: bytes) -> FlooMessage:
        msgLen = len(pkt)
        if msgLen < 2:
            return None
        msgHeader = pkt[:2].decode("ascii")
        if msgHeader in FlooParser.MSG_HEADERS:
            logger.debug("create a %s message", msgHeader)
            return FlooParser.MSG_HEADERS[msgHeader](pkt)
        else:
            return FlooMsgUnknown(False)

    def run(self, pkt: bytes) -> FlooMessage:
        return self.create_valid_message(pkt)
