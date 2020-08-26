import threading
from datetime import timedelta, datetime
import time

class Loop():
    def __init__(self, root, name, interval, delay=5 ):
        self._loop_root = root
        self._loop_delay = delay
        self._loop_interval = None
        self._loop_name = name
        self._loop_thread = None
        self._last_run = None

    def start_loop(self):
        self._loop_thread = threading.Thread(target=self.loop)
        self._loop_thread.name = "Cloud"
        self._loop_thread.daemon = True
        self._loop_thread.start()

    def _loop_start(self):
        if self._root.loop:
            asyncio.set_event_loop(self._root.loop)
        try:
            self.loop_start()
        except:
            LOGGER.error("Error start loop %s, %s", self._loop_name, ex)
        while not self._loop_root._stopped.isSet():
            self._loop

    def loop_start(self):
        pass

    def loop(self):
        if self._last_run is None or \
            datetime.now() - self._last_run \
                        > self._loop_interval:
            self._last_run = datetime.now()
            self.loop_timer()
            time.sleep(self._loop_delay)

    def loop_timer(self):
        pass