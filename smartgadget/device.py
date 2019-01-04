from bluepy.btle import DefaultDelegate, \
    Peripheral, BTLEException, ScanEntry, \
    UUID, ADDR_TYPE_RANDOM

import binascii
import time
import logging
from smartgadget.services import Float32Service, Uint8Service, LoggingService

log = logging.getLogger(__name__)


class SmartGadget(DefaultDelegate):

    def __init__(self, device):

        self.present = True
        self.peripheral = None

        if isinstance(device, ScanEntry):
            self.addr, self.addrType, self.iface = device.addr, device.addrType, device.iface
        else:
            self.addr, self.addrType, self.iface = device, ADDR_TYPE_RANDOM, None

        self.Temperature = Float32Service("00002234-b38d-4985-720e-0f993a68ee41")
        self.RelativeHumidity = Float32Service("00001234-b38d-4985-720e-0F993a68ee41",
                                               unit="%")

        self.Battery = Uint8Service("180F", unit="%")

        self.subscribable_services = [self.Temperature, self.RelativeHumidity]

        self.Logging = LoggingService("0000f234-b38d-4985-720e-0f993a68ee41",
                                      subscribables=self.subscribable_services)

    def connect(self):
        log.info("connect to '{}'...".format(self.addr))
        self.peripheral = Peripheral(self.addr, self.addrType, self.iface)
        self.peripheral.withDelegate(self)
        self.Temperature.connect(self.peripheral)
        self.RelativeHumidity.connect(self.peripheral)
        self.Battery.connect(self.peripheral)
        self.Logging.connect(self.peripheral)
        log.info("connected to '{}'!".format(self.addr))

    def is_connected(self):
        if self.peripheral is None: return False
        try:
            self.peripheral.status()
            return True
        except BTLEException:
            return False

    def handleNotification(self, cHandle, data):
        log.debug("received data: handle={}, data={}".format(cHandle, binascii.b2a_hex(data).decode('utf-8')))
        for service in self.subscribable_services:
            if cHandle == service.getHandle():
                return service.call_listeners(data)

    def listen_for_notifications(self, seconds=None):
        if seconds is None:
            while True:
                if self.peripheral.waitForNotifications(1.0):
                    continue
        else:
            t0 = time.time()
            while time.time() - t0 < seconds:
                if self.peripheral.waitForNotifications(1.0):
                    continue

    def __str__(self):
        return "Sensirion SmartGadget ({})".format(self.addr)

    def subscribe_temperature(self):
        self.Temperature.subscribe()

    def subscribe_relative_humidity(self):
        self.RelativeHumidity.subscribe()

    def subscribe_battery_level(self):
        self.Battery.subscribe()

    def read_temperature(self):
        return self.Temperature.read()

    def read_relative_humidity(self):
        return self.RelativeHumidity.read()

    def read_battery_level(self):
        return self.Battery.read()

    def download_temperature_and_relative_humidity(self, timeout=15):
        if not self.is_connected():
            raise Exception("Gadget is not connected!")
        self.Temperature.subscribe()
        self.RelativeHumidity.subscribe()

        self.Logging.start_download()

        t0 = time.time()
        while self.Logging.downloading:
            self.listen_for_notifications(0.5)
            if self.Logging.downloading:
                log.info("downloading {:.0f}%".format(self.Logging.progress()))
            if (time.time()-t0) > timeout:
                break

        self.Temperature.unsubscribe()
        self.RelativeHumidity.unsubscribe()

        return self.Logging.data

    def disconnect(self):
        log.info("Disconnect from {}...".format(self.addr))
        if self.peripheral is not None:
            self.peripheral.disconnect()
        log.info("Disconnected from {}...".format(self.addr))
