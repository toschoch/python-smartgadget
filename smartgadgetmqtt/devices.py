from bluepy.btle import Service, DefaultDelegate, ScanEntry, Peripheral, UUID, BTLEException, ADDR_TYPE_PUBLIC
import struct
import time
import logging

log = logging.getLogger(__name__)

class BTLEDevice(Peripheral):

    def __init__(self, deviceAddr, addrType=ADDR_TYPE_PUBLIC, iface=None):
        Peripheral.__init__(self, deviceAddr, addrType, iface)


    def _assure_connection(self):
        log.debug("check btle connection ({})".format(self.addr))
        if not self.is_connected():
            log.debug("device disconnected. Try to reconnect...")
            self.connect()
        log.debug("connection ok! ({})".format(self.addr))

    def connect(self):
        Peripheral.connect(self, self.addr, self.addrType)

    def is_connected(self):
        try:
            self.status()
            return True
        except BTLEException:
            return False

class LoggingService(object):

    def __init__(self, srv : Service):
        self._srv = srv
        chars = srv.getCharacteristics()
        assert len(chars) == 5
        self.SyncTimeMs = chars[0]
        self.OldestTimestampMs = chars[1]
        self.NewestTimestampMs = chars[2]
        self.StartLoggerDownload = chars[3]
        self.LoggerIntervalMs = chars[4]

    def retrieve(self):
        self.SyncTimeMs.write(b'\xd2\x1fPpg\x01\x00\x00')
        self.OldestTimestampMs.write(b'\x00\x00\x00\x00\x00\x00\x00\x00')
        self.NewestTimestampMs.write(b'\xd2\x1fPpg\x01\x00\x00')
        self.NewestTimestampMs.read()
        self.StartLoggerDownload.write(b'\x01\x00\x00\x00\x00\x00\x00\x00')


class SubscribableService(object):

    def __init__(self, srv: Service):
        self._srv = srv
        self.characteristic = srv.getCharacteristics()[0]
        self.handle = self.characteristic.getHandle()
        self.subscription_handle = self.handle + 1

    @staticmethod
    def format_data(data):
        return data[0]

    def read(self):
        return self.format_data(self.characteristic.read())

    def subscribe(self):
        self._srv.peripheral.writeCharacteristic(self.subscription_handle, b'\x01\x00')

    def unsubscribe(self):
        self._srv.peripheral.writeCharacteristic(self.subscription_handle, b'\x00\x00')

class ValueService(SubscribableService):

    def __init__(self, srv : Service):
        self._srv = srv
        self.characteristic = srv.getCharacteristics()[0]
        self.handle = self.characteristic.getHandle()
        self.description_handle = self.handle + 1
        self.subscription_handle = self.handle + 2
        self._cached_description = self.readDescription()

    def read(self):
        return self.format_data(self.characteristic.read())

    @staticmethod
    def format_data(data):
        return struct.unpack('<f', data)[0]

    def readDescription(self):
        return self._srv.peripheral.readCharacteristic(self.description_handle).decode('utf-8')

    @property
    def description(self):
        return self._cached_description



class HumiGadget(BTLEDevice, DefaultDelegate):

    def __init__(self, deviceAddr, addrType, iface=None):
        BTLEDevice.__init__(self, deviceAddr, addrType, iface)
        self.Temperature = ValueService(self.getServiceByUUID(UUID("00002234-b38d-4985-720e-0f993a68ee41")))
        self.RelativeHumidity = ValueService(self.getServiceByUUID(UUID("00001234-b38d-4985-720e-0F993a68ee41")))

        self.Battery = SubscribableService(self.getServiceByUUID(UUID("180F")))

        self.Logging = LoggingService(self.getServiceByUUID(UUID("0000f234-b38d-4985-720e-0f993a68ee41")))

        self.withDelegate(self)

    def handleNotification(self, cHandle, data):
        if cHandle == self.Temperature.handle:
            log.info("Temperature: {:.2f}°C".format(self.Temperature.format_data(data)))
        elif cHandle == self.RelativeHumidity.handle:
            log.info("Relative Humidity: {:.2f}%".format(self.RelativeHumidity.format_data(data)))
        elif cHandle == self.Battery.handle:
            log.info("Battery Level: {:d}%".format(self.Battery.format_data(data)))

    def listenForNotifications(self, seconds=None):
        if seconds is None:
            while True:
                if self.waitForNotifications(1.0):
                    continue
        else:
            t0 = time.time()
            while time.time() - t0 < 20:
                if self.waitForNotifications(1.0):
                    continue

    def subscribeTemperature(self):
        self.Temperature.subscribe()

    def subscribeRelativeHumidity(self):
        self.RelativeHumidity.subscribe()

    def subscribeBatteryLevel(self):
        self.Battery.subscribe()

    def readTemperature(self):
        return self.Temperature.read()

    def readRelativeHumidity(self):
        return self.RelativeHumidity.read()

    def readBatteryLevel(self):
        return self.Battery.read()