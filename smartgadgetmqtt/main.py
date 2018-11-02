from bluepy.btle import Scanner, DefaultDelegate, ScanEntry, Peripheral, UUID, ADDR_TYPE_RANDOM
import struct
import time
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

if __name__ == '__main__':
    import devices as devs

    class ScanDelegate(DefaultDelegate):
        def __init__(self):
            DefaultDelegate.__init__(self)
            self.gadgets = []


        def handleDiscovery(self, dev, isNewDev, isNewData):
            if isNewDev:
                for (a, d, v) in dev.getScanData():
                    if d == "Complete Local Name" and v=="Smart Humigadget":
                        print("Discovered humigadget", dev.addr, dev.rssi)
                        self.gadgets.append(dev)
                print("Discovered device", dev.addr)
            elif isNewData:
                print("Received new data from", dev.addr)



    delegate = ScanDelegate()
    scanner = Scanner().withDelegate(delegate)
    devices = scanner.scan(10.0)

    for dev in delegate.gadgets:
        print("Device %s (%s), RSSI=%d dB" % (dev.addr, dev.addrType, dev.rssi))
        for (adtype, desc, value) in dev.getScanData():
            print("  %s = %s" % (desc, value))
        print("  connectable: %s" % dev.connectable)

    ph = devs.HumiGadget('f2:70:95:f3:43:44', ADDR_TYPE_RANDOM)
#     ph.discoverServices()
#     srvs = ph.getServices()
#     for srv in srvs:
#         print("Service: %s" % srv.uuid)
#         for ch in srv.getCharacteristics():
#             print("   %s (%s)" % (ch, ch.propertiesToString()))
#             if ch.supportsRead():
# #                value = struct.unpack('<f',ch.read())
#                 print("   = %s" % ch.read())


    print("T=%.2f°C"%ph.readTemperature())
    print("RH=%.2f%%"%ph.readRelativeHumidity())
    b = ph.readBatteryLevel()
    print("battery=%d%%"%b)

    t0 = time.time()
    #ph.subscribeTemperature()
    #ph.subscribeRelativeHumidity()
    #ph.subscribeBatteryLevel()
    ph.listenForNotifications(20)




    ph.disconnect()
