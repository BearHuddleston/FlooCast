import time

import serial
import serial.tools.list_ports

from floocast.protocol.messages import FlooMessage
from floocast.protocol.parser import FlooParser


class FlooInterface:
    """FlooGoo Bluetooth USB Dongle Control Interface on USB COM port"""

    def __init__(self, delegate):
        super().__init__()
        self.delegate = delegate
        self.isSleep = False
        self.port_name = None
        self.port_opened = False
        self.port_locked = False
        self.port = None
        self.parser = FlooParser()

    def setSleep(self, flag):
        self.isSleep = flag

    def reset(self):
        print("FlooInterface: reset")
        if self.port_opened:
            print("FlooInterface: close port")
            self.port.close()
        # self.port_name = None
        self.port_opened = False
        self.port = None
        self.delegate.interfaceState(False, None)

    def monitor_port(self) -> bool:
        if self.isSleep:
            return False

        print([port.hwid for port in serial.tools.list_ports.grep("0A12:4007.*FMA120.*")])
        ports = [
            port.name for port in serial.tools.list_ports.grep("0A12:4007.*FMA120.*")
        ]  # FMA120
        if ports:
            if not self.port_opened:
                self.port_name = ports[0]
                print("monitor_port: try open " + self.port_name)
                try:
                    self.port = serial.Serial(
                        port="/dev/" + self.port_name,
                        baudrate=921600,
                        bytesize=8,
                        timeout=2,
                        stopbits=serial.STOPBITS_ONE,
                        exclusive=True,
                    )
                    self.port_opened = self.port.is_open
                    if self.port_opened:
                        self.port_locked = False
                        self.delegate.interfaceState(True, self.port_name)
                    return self.port_opened
                except Exception as e:
                    err_str = str(e).lower()
                    if (
                        "lock" in err_str
                        or "busy" in err_str
                        or "unavailable" in err_str
                        or "use" in err_str
                        or "permission" in err_str
                    ):
                        self.delegate.connectionError("port_busy")
                        self.port_locked = True
                    else:
                        print(f"Port error: {e}")
                        self.delegate.connectionError("port_error")
                        self.reset()
                    return False
        else:
            if self.port_opened:
                print("monitor_port: no port exists")
                self.reset()
        return False

    def run(self):
        MAX_CONSECUTIVE_FAILURES = 3
        while True:
            if self.monitor_port():
                consecutive_failures = 0
                while self.port is not None and self.port.is_open and not self.isSleep:
                    try:
                        if self.port.inWaiting() > 0:
                            newLine = self.port.read_until(b"\r\n")
                            payload = newLine[:-2]
                            if len(payload) < 2:
                                continue
                            flooMsg = self.parser.run(payload)
                            if flooMsg is None:
                                consecutive_failures += 1
                                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                                    break
                                continue
                            consecutive_failures = 0
                            self.delegate.handleMessage(flooMsg)
                        time.sleep(0.01)
                    except Exception as exec0:
                        print(exec0)
                        self.portOpenDelay = None
                        self.reset()
            elif not self.port_locked:
                self.reset()
            time.sleep(5 if self.port_locked else 1)

    def sendMsg(self, msg: FlooMessage):
        if self.port is not None and self.port.is_open and not self.isSleep:
            try:
                print("FlooInterface: send " + msg.bytes.decode())
                self.port.write(msg.bytes)
            except Exception as exec0:
                print(exec0)
