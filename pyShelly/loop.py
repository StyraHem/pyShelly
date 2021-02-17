import threading
from datetime import timedelta, datetime
import time

from .const import (
    LOGGER
)

class Loop(object):
    def __init__(self, name, root, interval=None, delay=5 ):
        self._loop_root = root
        self._loop_delay = delay
        self._loop_interval = interval
        self._loop_name = name
        self._loop_thread = None
        self._last_run = None
        self._force_stop = False

    def start_loop(self):
        self._loop_thread = threading.Thread(target=self._start_loop)
        self._loop_thread.name = self._loop_name
        self._loop_thread.daemon = True
        self._loop_thread.start()

    def stop_loop(self):
        self._force_stop = True


    def _start_loop(self):
        try:
            self.loop_started()
        except:
            LOGGER.exception("Error start loop %s, %s", self._loop_name)
        while not self._loop_root.stopped.isSet() and not self._force_stop:
            try:
                self.loop()
            except:
                LOGGER.exception("Error in loop " + self._loop_name)
        try:
            self.loop_stopped()
        except:
            LOGGER.exception("Error stop loop %s, %s", self._loop_name)

    def loop_started(self):
        pass

    def loop_stopped(self):
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