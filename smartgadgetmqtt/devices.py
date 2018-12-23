from bluepy.btle import Service as _Service, DefaultDelegate, \
    Peripheral, UUID, BTLEException, ScanEntry, Characteristic as _Characteristic, Descriptor, \
    ADDR_TYPE_PUBLIC, ADDR_TYPE_RANDOM

import struct
import time
import logging
import datetime

log = logging.getLogger(__name__)


class BLEDevice(Peripheral):

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


class Characteristic(_Characteristic):

    def __init__(self,
                 characteristic: _Characteristic,
                 description_handle_offset=None,
                 byte_format=None, nbytes=1):

        _Characteristic.__init__(self,
                                 characteristic.peripheral,
                                 characteristic.uuid,
                                 characteristic.handle,
                                 characteristic.properties,
                                 characteristic.valHandle)

        self.byte_format = byte_format
        self.nbytes = nbytes

        if description_handle_offset is None:
            self._description_read = self.uuid.getCommonName
        else:
            self._description_desc = Descriptor(self.peripheral, self.uuid, self.valHandle + description_handle_offset)
            self._description_read = self._description_desc.read

        self._description_cache = self.description_read()

    def unpack_data(self, bytes):

        if self.byte_format:
            bytes = struct.unpack(self.byte_format, bytes)
            assert len(bytes) == self.nbytes
            if self.nbytes == 1:
                bytes = bytes[0]

        return bytes

    def pack_data(self, data):

        if self.byte_format:
            data = struct.pack(self.byte_format, data)

        return data

    def read(self):
        data = _Characteristic.read(self)
        return self.unpack_data(data)

    def write(self, value, with_response=False):
        data = self.pack_data(value)
        return _Characteristic.write(self, data, with_response)

    def description_read(self):
        description = self._description_read()
        if isinstance(description, bytes):
            return description.decode('utf-8')
        return description

    @property
    def description(self):
        return self._description_cache


class SubscribableCharacteristic(Characteristic):

    def __init__(self,
                 characteristic: _Characteristic,
                 subscription_handle_offset=1,
                 listener_list=None,
                 *args, **kwargs):
        Characteristic.__init__(self, characteristic, *args, **kwargs)
        self.listener_list = listener_list
        self.subscription = Descriptor(self.peripheral, self.uuid, self.valHandle + subscription_handle_offset)

    def subscribe(self):
        if self.listener_list is not None and self not in self.listener_list:
            self.listener_list.append(self)
        self.subscription.write(b'\x01\x00')

    def unsubscribe(self):
        self.subscription.write(b'\x00\x00')
        if self.listener_list is not None and self in self.listener_list:
            self.listener_list.remove(self)

    @property
    def subscribed(self):
        return self.subscription.read() != b'\x00\x00'


class Uint8Service(SubscribableCharacteristic):

    def __init__(self, srv: _Service, *args, **kwargs):
        SubscribableCharacteristic.__init__(self,
                                            characteristic=srv.getCharacteristics()[0],
                                            byte_format='<B',
                                            nbytes=1, *args, **kwargs)


class Float32Service(SubscribableCharacteristic):

    def __init__(self, srv: _Service, *args, **kwargs):
        SubscribableCharacteristic.__init__(self,
                                            characteristic=srv.getCharacteristics()[0],
                                            description_handle_offset=1,
                                            subscription_handle_offset=2,
                                            byte_format='<f',
                                            nbytes=1, *args, **kwargs)


class LoggingService(object):

    n_samples_to_download: int

    def __init__(self, srv: _Service, *args, **kwargs):
        chars = srv.getCharacteristics()
        assert len(chars) == 5
        self.peripheral = srv.peripheral

        self.SyncTimeMs = Characteristic(chars[0],
                                         description_handle_offset=1,
                                         byte_format='<Q', *args, **kwargs)
        self.OldestTimestampMs = Characteristic(chars[1],
                                                description_handle_offset=1,
                                                byte_format='<Q', *args, **kwargs)
        self.NewestTimestampMs = Characteristic(chars[2],
                                                description_handle_offset=1,
                                                byte_format='<Q', *args, **kwargs)
        self.StartLoggerDownload = Characteristic(chars[3],
                                                  description_handle_offset=1,
                                                  byte_format='<B', *args, **kwargs)
        self.LoggerIntervalMs = Characteristic(chars[4],
                                               description_handle_offset=1,
                                               byte_format='<I', *args, **kwargs)

        self.data = []
        self.oldest_time = 0
        self.newest_time = 0
        self.interval = 0

        self.n_samples_to_download = 0
        self.n_samples_downloaded = 0

    @property
    def description(self):
        return "Logging Service"

    def start_download(self):

        log.info("initiate download....")

        interval = self.LoggerIntervalMs.read()
        log.info("read logging interval: {0} ms".format(interval))

        self.OldestTimestampMs.write(0)
        log.info("wrote oldest timestamp: {0} ms".format(0))

        time_ms = int(time.time_ns() / 1000000.)
        self.SyncTimeMs.write(time_ms)
        log.info("wrote sync time: {} ms".format(time_ms))

        time.sleep(0.5)

        newest_time = self.NewestTimestampMs.read()
        log.info("read newest timestamp: {0} ms".format(newest_time))

        oldest_time = self.OldestTimestampMs.read()
        log.info("read oldest timestamp: {0} ms".format(oldest_time))

        n_samples_to_download = int((newest_time - oldest_time) / interval)
        logging_time = datetime.timedelta(milliseconds=newest_time - oldest_time)
        log.info("devices has {} samples ({}) in memory".format(n_samples_to_download, logging_time))

        log.info("start download....")
        self.data.clear()
        self.oldest_time = oldest_time
        self.newest_time = newest_time
        self.interval = interval
        # set the delegate temporary to the logging service
        self.peripheral.withDelegate(self)
        self.n_samples_to_download = n_samples_to_download
        self.StartLoggerDownload.write(1)

    def _sample_number_to_time(self, sample):
        return self.newest_time - (self.n_samples_to_download - sample) * self.interval

    def handleNotification(self, cHandle, data):

        log.debug("arrived a download notification: {}".format(cHandle))
        log.debug("data length: {}".format(len(data)))

        if len(data)<=4:
            return self.peripheral.handleNotification(cHandle, data)

        seq_number = struct.unpack('<I',data[:4])[0]
        log.debug("sequence {} arrived!".format(seq_number))

        if seq_number != self.n_samples_downloaded+1:

            log.warning("download missed sequence {}! Continue with sequence {}".format(self.n_samples_downloaded+1,
                                                                                        seq_number))

        assert (len(data) - 4) % 4 == 0
        seq_length = (len(data) - 4) // 4

        stream = list((self._sample_number_to_time(seq_number + i-1), d[0]) for i, d in enumerate(struct.iter_unpack('<f',data[4:])))
        assert len(stream) == seq_length
        self.data.extend(stream)

        log.debug("sequence: {}".format(stream))

        self.n_samples_downloaded = seq_number + seq_length - 1

        if (self.n_samples_to_download - self.n_samples_downloaded) == 0:
            self.on_download_finished()
        elif (self.n_samples_to_download - self.n_samples_downloaded) < 0:
            self.on_download_failed()


    def on_download_failed(self):
        pass
        self.on_download_finished()

    def on_download_finished(self):
        self.StartLoggerDownload.write(0)
        self.peripheral.withDelegate(self.peripheral)
        log.info("Download finished! (expected: {}, downloaded: {}, {})".format(self.n_samples_to_download,
                                                                            len(self.data),
                                                                            self.n_samples_downloaded))
        self.n_samples_to_download = 0
        self.n_samples_downloaded = 0

    @property
    def downloading(self):
        return self.n_samples_to_download > 0

    def progress(self):
        if self.n_samples_to_download > 0:
            return float(self.n_samples_downloaded)*100./self.n_samples_to_download
        else:
            return 0

class SmartGadget(BLEDevice, DefaultDelegate):

    def __init__(self, device, addr_type=ADDR_TYPE_RANDOM, iface=None):

        if isinstance(device, ScanEntry):
            log.info("Connect to {}...".format(device.addr))
        else:
            log.info("Connect to {}...".format(device))

        BLEDevice.__init__(self, device, addr_type, iface)
        log.info("Connected to {}!".format(device))

        self.listeners = []

        self.Temperature = Float32Service(self.getServiceByUUID(UUID("00002234-b38d-4985-720e-0f993a68ee41")),
                                          listener_list=self.listeners)
        self.RelativeHumidity = Float32Service(self.getServiceByUUID(UUID("00001234-b38d-4985-720e-0F993a68ee41")),
                                               listener_list=self.listeners)

        self.Battery = Uint8Service(self.getServiceByUUID(UUID("180F")),
                                    listener_list=self.listeners)

        self.Logging = LoggingService(self.getServiceByUUID(UUID("0000f234-b38d-4985-720e-0f993a68ee41")))

        for service in [self.Temperature, self.RelativeHumidity, self.Battery, self.Logging]:
            log.debug("Initiated: {}".format(service.description))

        self.withDelegate(self)

    def handleNotification(self, cHandle, data):
        for listener in self.listeners:
            if cHandle == listener.getHandle():

                if listener is self.Temperature:
                    log.info("Temperature: {:.2f}°C".format(self.Temperature.unpack_data(data)))
                    return

                if listener is self.RelativeHumidity:
                    log.info("Relative Humidity: {:.2f}%".format(self.RelativeHumidity.unpack_data(data)))
                    return

                if listener is self.Battery:
                    log.info("Battery Level: {:d}%".format(self.Battery.unpack_data(data)))
                    return

        log.info("received data: handle={}, data={}".format(cHandle, data))

    def listen_for_notifications(self, seconds=None):
        if seconds is None:
            while True:
                if self.waitForNotifications(1.0):
                    continue
        else:
            t0 = time.time()
            while time.time() - t0 < seconds:
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
        BLEDevice.disconnect(self)
        log.info("Disconnected from {}...".format(self.addr))
