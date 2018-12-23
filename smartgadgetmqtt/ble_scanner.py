from bluepy.btle import DefaultDelegate, Scanner
import logging

log = logging.getLogger(__name__)

class SmartGadgetScanner(DefaultDelegate):
    def __init__(self, gadgets=[]):
        DefaultDelegate.__init__(self)
        self._gadgets = gadgets


    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            for (a, d, v) in dev.getScanData():
                if d == "Complete Local Name" and v== "Smart Humigadget":
                    log.info("Discovered smart gadget ({0}, {1} db)...".format(dev.addr, dev.rssi))
                    self._gadgets.append(dev)
            log.debug("Discovered device ({0}, {1} db)...".format(dev.addr, dev.rssi))
        elif isNewData:
            log.debug("Received new data from {0}...".format(dev.addr))

    def scan(self, seconds=10.0):
        #self._gadgets.clear()
        scanner = Scanner().withDelegate(self)
        scanner.scan(seconds)
        return self._gadgets
