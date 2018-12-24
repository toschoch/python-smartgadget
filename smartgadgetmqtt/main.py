from bluepy.btle import Scanner, ADDR_TYPE_RANDOM
import time
import struct
import logging
from queue import Queue
import apscheduler as aps
from smartgadgetmqtt import devices as devs
from smartgadgetmqtt import ble_scanner as sc

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

if __name__ == '__main__':

    gadgets = sc.SmartGadgetScanner().scan()

    ph = devs.SmartGadget('f2:70:95:f3:43:44')
    #ph2 = devs.SmartGadget('e2:07:bc:53:40:61')

    print("T=%.2f%s" % (ph.read_temperature(), ph.Temperature.unit))
    print("RH=%.2f%s" % (ph.read_relative_humidity(), ph.RelativeHumidity.unit))
    b = ph.read_battery_level()
    print("battery=%d%%"%b)

    #ph.subscribe_battery_level()
    ph.subscribe_relative_humidity()

    ph.Temperature.register_listener(lambda v, srv: logging.info("Temperature: {:.2f}{}".format(v, srv.unit)))
    ph.RelativeHumidity.register_listener(lambda v, srv: logging.info("Humidity: {:.2f}{}".format(v, srv.unit)))

    ph.subscribe_temperature()

    ph.Logging.start_download()

    while ph.Logging.downloading:
        ph.listen_for_notifications(0.5)
        if ph.Logging.downloading:
            logging.info("downloading {:.0f}%".format(ph.Logging.progress()))

    print(len(ph.Logging.data))
    print(len(list(ph.Logging.data.values())[0]))
    print(ph.Logging.data)

    ph.listen_for_notifications(5)
