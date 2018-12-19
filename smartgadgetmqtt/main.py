from bluepy.btle import Scanner, ADDR_TYPE_RANDOM
import time
import struct
import logging
from queue import Queue
import apscheduler as aps

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

if __name__ == '__main__':
    import devices as devs
    import ble_scanner as sc

    gadgets = sc.SmartGadgetScanner().scan()

    for dev in gadgets:
        print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
        for (adtype, desc, value) in dev.getScanData():
            print("  %s = %s" % (desc, value))
        print("  connectable: %s" % dev.connectable)

    ph = devs.HumiGadget('f2:70:95:f3:43:44', ADDR_TYPE_RANDOM)

    print("T=%.2f°C"%ph.readTemperature())
    print("RH=%.2f%%"%ph.readRelativeHumidity())
    b = ph.readBatteryLevel()
    print("battery=%d%%"%b)

    t0 = time.time()
    ph.Logging.retrieve()
    logging.info("start logging download...")

    ph.listenForNotifications(20)
    #ph.subscribeTemperature()

    #ph.subscribeRelativeHumidity()
    #ph.subscribeBatteryLevel()
    time.sleep(10)
    logging.info("stop logging download...")

    ph.disconnect()
