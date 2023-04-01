from pyShelly import pyShelly
from datetime import timedelta, datetime
import logging
import os, sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
LOGGER = logging.getLogger('pyShelly-run')

def device_added(dev,code):
  LOGGER.info("Device added: " + str(dev) + " " + dev.friendly_name())

shelly = pyShelly()
shelly.update_status_interval = timedelta(seconds=60)

# enable sync with data in cloud (e.g. to get the device's room name) by configuring cloud settings
shelly.set_cloud_settings(os.environ.get('SHELLY_HOST'), os.environ.get('SHELLY_AUTH_KEY'))

shelly.prometheus_enabled = True

shelly.cb_device_added.append(device_added)
shelly.start()
# the below could be used to add a Shelly Plug S which is running in factory mode 
# alternatively devices could be discovered (CoAP) using shelly.discover()
shelly_ips = os.environ.get('SHELLY_IPS').split(",")
for shelly_ip in shelly_ips:
  shelly.add_device_by_ip(shelly_ip, "IP-addr")
# shelly.discover()

while True:
    pass
