from bluepy.btle import Service, DefaultDelegate, \
    Peripheral, UUID, BTLEException, ScanEntry, Characteristic as BTLECharacteristic, \
    ADDR_TYPE_PUBLIC, ADDR_TYPE_RANDOM

import struct
import time
import logging

log = logging.getLogger(__name__)


class BTLEDevice(Peripheral):

    def __init__(self, device_addr, addr_type=ADDR_TYPE_PUBLIC, iface=None):
        Peripheral.__init__(self, device_addr, addr_type, iface)

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


class Characteristic(object):

    def __init__(self, characteristic: BTLECharacteristic):
        self._original_characteristic = characteristic
        self.write_handle = self.handle + 1

    def read(self):
        return self._original_characteristic.read()

    def write(self, value, with_response=False):
        return self.peripheral.writeCharacteristic(self.write_handle,
                                                        val=value,
                                                        withResponse=with_response)

    @property
    def handle(self):
        return self._original_characteristic.getHandle()

    @property
    def peripheral(self):
        return self._original_characteristic.peripheral


class DescribedCharacteristic(Characteristic):

    def __init__(self, characteristic: BTLECharacteristic):
        Characteristic.__init__(self, characteristic)
        self.description_handle = self.handle + 1
        self.write_handle = self.handle + 2
        self._cached_description = self.read_description()

    def read_description(self):
        return self._original_characteristic.peripheral.readCharacteristic(self.description_handle).decode('utf-8')

    @property
    def description(self):
        return self._cached_description


class LoggingService(object):

    def __init__(self, srv: Service):
        chars = srv.getCharacteristics()
        assert len(chars) == 5
        self.SyncTimeMs = DescribedCharacteristic(chars[0])
        self.OldestTimestampMs = DescribedCharacteristic(chars[1])
        self.NewestTimestampMs = DescribedCharacteristic(chars[2])
        self.StartLoggerDownload = DescribedCharacteristic(chars[3])
        self.LoggerIntervalMs = DescribedCharacteristic(chars[4])

    def start_download(self):
        log.info("initiate download....")
        interval = self.LoggerIntervalMs.read()
        interval = struct.unpack('<I', interval)[0]
        log.info("read logging interval: {0} ms".format(interval))

        self._srv.peripheral.writeCharacteristic(self.OldestTimestampMs.valHandle, struct.pack('<Q', 0))
        log.info("wrote oldest timestamp: {0} ms".format(0))

        oldest_time = self.OldestTimestampMs.read()
        oldest_time = struct.unpack('<Q', oldest_time)[0]
        log.info("read oldest timestamp: {0} ms".format(oldest_time))

        time_ms = int(time.time_ns() / 1000000.)
        self._srv.peripheral.writeCharacteristic(self.SyncTimeMs.valHandle, struct.pack('<Q', time_ms))
        log.info("wrote sync time: {} ms".format(time_ms))

        newest_time = self.NewestTimestampMs.read()
        newest_time = struct.unpack('<Q', newest_time)[0]
        log.info("read newest timestamp: {0} ms".format(newest_time))
        log.info("start download....")
        self._srv.peripheral.writeCharacteristic(self.StartLoggerDownload.handle, struct.pack('<B', 1))


class SubscribableService(object):

    def __init__(self, srv: Service):
        self.characteristic = Characteristic(srv.getCharacteristics()[0])

    @property
    def handle(self):
        return self.characteristic.handle

    @staticmethod
    def format_data(data):
        return data[0]

    def read(self):
        return self.format_data(self.characteristic.read())

    def subscribe(self):
        self.characteristic.write(b'\x01\x00')

    def unsubscribe(self):
        self.characteristic.write(b'\x00\x00')


class ValueService(SubscribableService):

    def __init__(self, srv: Service):
        self.characteristic = DescribedCharacteristic(srv.getCharacteristics()[0])

    def read(self):
        return self.format_data(self.characteristic.read())

    @staticmethod
    def format_data(data):
        return struct.unpack('<f', data)[0]

    @property
    def description(self):
        return self.characteristic.description


class SmartGadget(BTLEDevice, DefaultDelegate):

    def __init__(self, device, addr_type=ADDR_TYPE_RANDOM, iface=None):

        if isinstance(device, ScanEntry):
            log.info("Connect to {}...".format(device.addr))
        else:
            log.info("Connect to {}...".format(device))
        BTLEDevice.__init__(self, device, addr_type, iface)
        log.info("Connected to {}!".format(device))

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
        else:
            log.info("received data: handle={}, data={}".format(cHandle, data))

    def listen_for_notifications(self, seconds=None):
        if seconds is None:
            while True:
                if self.waitForNotifications(1.0):
                    continue
        else:
            t0 = time.time()
            while time.time() - t0 < 20:
                if self.waitForNotifications(1.0):
                    continue

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

    def disconnect(self):
        log.info("Disconnect from {}...".format(self.addr))
        BTLEDevice.disconnect(self)
        log.info("Disconnected from {}...".format(self.addr))
