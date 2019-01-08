from bluepy.btle import DefaultDelegate, Scanner
from .device import SmartGadget
import logging
log = logging.getLogger(__name__)


def is_smartgadget(dev):
    for (a, d, v) in dev.getScanData():
        if d == "Complete Local Name" and v== "Smart Humigadget":
            return True
    return False


class SmartGadgetScanner(DefaultDelegate, Scanner):
    def __init__(self, iface=0, store={}):
        DefaultDelegate.__init__(self)
        Scanner.__init__(self, iface=iface)
        self.gadgets = store
        self._gadgets = {}
        self.withDelegate(self)

    def handleDiscovery(self, dev, isNewDev, isNewData):
        if isNewDev:
            if is_smartgadget(dev):
                log.debug("Discovered smart gadget ({0}, {1} db)...".format(dev.addr, dev.rssi))
                self._gadgets[dev.addr] = SmartGadget(dev)
                dev.present = True
                return
            log.debug("Discovered device ({0}, {1} db)...".format(dev.addr, dev.rssi))
        elif isNewData:
            log.debug("Received new data from {0}...".format(dev.addr))

    def on_appearance(self, dev):
        pass

    def on_disappearance(self, dev):
        pass

    def scan(self, timeout=10, passive=False):
        Scanner.scan(self, timeout, passive)
        for addr, dev in self.gadgets.items():
            if (not dev.present) or dev.is_connected(): continue
            if addr not in self._gadgets:
                self.on_disappearance(dev)
                dev.present = False

        for addr, dev in self._gadgets.items():
            if addr not in self.gadgets or (not self.gadgets[addr].present):
                self.on_appearance(dev)
                dev.present = True
                self.gadgets[addr] = dev
        self._gadgets.clear()
