from pyShelly import pyShelly
from datetime import timedelta, datetime

def device_added(dev,code):
  print (dev," ",code)

shelly = pyShelly()
shelly.update_status_interval = timedelta(seconds=300)

# enable sync with data in cloud (e.g. to get the device's room name) by configuring cloud settings
# shelly.set_cloud_settings(os.environ.get('SHELLY_HOST'), os.environ.get('SHELLY_AUTH_KEY'))

shelly.prometheus_enabled = True

shelly.cb_device_added.append(device_added)
shelly.start()
# the below could be used to add a Shelly Plug S which is running in factory mode 
# alternatively devices could be discovered (CoAP) using shelly.discover()
shelly.add_device_by_ip("192.168.33.1", "IP-addr")

while True:
    pass
