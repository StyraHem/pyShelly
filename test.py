from pyShelly import pyShelly
from datetime import timedelta, datetime

def device_added(dev,code):
  print (dev," ",code)

shelly = pyShelly()
shelly.update_status_interval = timedelta(seconds=300)

shelly.prometheus_enabled = True

shelly.cb_device_added.append(device_added)
shelly.start()
shelly.add_device_by_ip("192.168.33.1", "IP-addr")

while True:
    pass
