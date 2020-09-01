import threading
from datetime import timedelta, datetime
import time

class Loop():
    def __init__(self, name, root, interval, delay=5 ):
        self._loop_root = root
        self._loop_delay = delay
        self._loop_interval = interval
        self._loop_name = name
        self._loop_thread = None
        self._last_run = None

    def start_loop(self):
        self._loop_thread = threading.Thread(target=self._loop_start)
        self._loop_thread.name = self._loop_name
        self._loop_thread.daemon = True
        self._loop_thread.start()

    def _loop_start(self):
        try:
            self.loop_start()
        except:
            LOGGER.error("Error start loop %s, %s", self._loop_name, ex)
        while not self._loop_root.stopped.isSet():
            self.loop()

    def loop_start(self):
        pass

    def loop(self):
        if self._last_run is None or \
            datetime.now() - self._last_run \
                        > self._loop_interval:
            self._last_run = datetime.now()
            self.loop_timer()
        self._loop_root.stopped.wait(self._loop_delay)

    def loop_timer(self):
        pass