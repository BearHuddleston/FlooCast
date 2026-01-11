import threading


class FlooDfuThread(threading.Thread):
    DFU_STATE_DONE = 101
    DFU_ERROR_NOT_SUPPORTED = 102

    def __init__(self, cmd, stateCallback):
        self.stateCallback = stateCallback
        threading.Thread.__init__(self)

    def run(self):
        self.stateCallback(FlooDfuThread.DFU_ERROR_NOT_SUPPORTED)
