from bluepy.btle import Scanner, ADDR_TYPE_RANDOM
import time
import struct
import logging
from queue import Queue
import apscheduler as aps

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

if __name__ == '__main__':
    import devices as devs
    import ble_scanner as sc

    gadgets = sc.SmartGadgetScanner().scan()

    ph = devs.SmartGadget('f2:70:95:f3:43:44')

    print("T=%.2f°C" % ph.read_temperature())
    print("RH=%.2f%%" % ph.read_relative_humidity())
    b = ph.read_battery_level()
    print("battery=%d%%"%b)


    #ph.subscribe_battery_level()
    #ph.subscribe_relative_humidity()
    ph.subscribe_temperature()
    ph.Logging.start_download()

    while ph.Logging.downloading:
        ph.listen_for_notifications(0.5)
        if ph.Logging.downloading:
            logging.info("downloading {:.0f}%".format(ph.Logging.progress()))

    print(len(ph.Logging.data))
    print(ph.Logging.data)

    ph.listen_for_notifications(5)
