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
                 unit=None,
                 byte_format=None, nbytes=1):

        _Characteristic.__init__(self,
                                 characteristic.peripheral,
                                 characteristic.uuid,
                                 characteristic.handle,
                                 characteristic.properties,
                                 characteristic.valHandle)

        self.byte_format = byte_format
        self.nbytes = nbytes
        self._unit = unit

        if description_handle_offset is None:
            self._description_read = self.uuid.getCommonName
        else:
            self._description_desc = Descriptor(self.peripheral, self.uuid, self.valHandle + description_handle_offset)
            self._description_read = self._description_desc.read

        self._description_cache = self.description_read()

    @property
    def unit(self):
        if self._unit is not None:
            return self._unit
        return self.description.split(' ')[-1]

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
                 *args, **kwargs):
        Characteristic.__init__(self, characteristic, *args, **kwargs)
        self._listeners = []
        self.subscription = Descriptor(self.peripheral, self.uuid, self.valHandle + subscription_handle_offset)
        self._subscribed = self.subscription.read() != b'\x00\x00'

    def subscribe(self):
        self.subscription.write(b'\x01\x00')
        self._subscribed = True

    def unsubscribe(self):
        self.subscription.write(b'\x00\x00')
        self._subscribed = False

    def register_listener(self, callback):
        self._listeners.append(callback)

    def unregister_listener(self, callback):
        self._listeners.remove(callback)

    def call_listeners(self, data):
        for listener in self._listeners:
            listener(self.unpack_data(data), self)

    @property
    def subscribed(self):
        return self._subscribed


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

    DOWNLOAD_TIMEOUT=10
    SEQUENCE_NUMBER_SIZE=4

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

        self._reset_download()

        self.data = {}
        self.n_samples_downloaded = {}
        self.n_samples_missed = {}

    def _reset_download(self):
        self.oldest_time = 0
        self.newest_time = 0
        self.interval = 0
        self.n_samples_to_download = 0

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
        self.oldest_time = oldest_time
        self.newest_time = newest_time
        self.interval = interval

        # set the delegate temporary to the logging service
        self.time_start_download = time.time()
        self.peripheral.withDelegate(self)

        # create counter and data storage for all subscribed services
        subscribed_services = [src for src in self.peripheral.subscribable_services if src.subscribed]
        self.n_samples_to_download = n_samples_to_download
        self.n_samples_downloaded = dict(zip(subscribed_services, [n_samples_to_download]*len(subscribed_services)))
        self.n_samples_missed = dict(zip(subscribed_services, [0]*len(subscribed_services)))
        self.data = dict(zip(subscribed_services, [[]]*len(subscribed_services)))

        self.StartLoggerDownload.write(1)

    def _sample_number_to_time(self, sample):
        return self.newest_time - sample * self.interval

    def handleNotification(self, cHandle, data):

        log.debug("arrived a download notification: {}".format(cHandle))
        log.debug("data length: {}".format(len(data)))

        for service in self.peripheral.subscribable_services:
            if cHandle == service.getHandle():
                return self._process_download_data(service, data)

    def _process_download_data(self, srv: Characteristic, data):

        if len(data)<=self.SEQUENCE_NUMBER_SIZE:
            if (time.time() - self.time_start_download) >= self.DOWNLOAD_TIMEOUT:
                self.on_download_failed()
            return srv.call_listeners(data)

        seq_number = struct.unpack('<I',data[:self.SEQUENCE_NUMBER_SIZE])[0]
        log.debug("sequence {} arrived!".format(seq_number))

        log.debug("description: {}".format(srv.description))
        next_seq_number = self.n_samples_downloaded[srv]+1

        if seq_number > next_seq_number:
            self.n_samples_missed[srv] += (seq_number - next_seq_number)
            log.warning("Download missed sequence {}! Continue with sequence {}".format(next_seq_number,
                                                                                        seq_number))

        size = struct.calcsize(srv.byte_format)
        seq_bytes = len(data) - self.SEQUENCE_NUMBER_SIZE
        seq_length = seq_bytes // size
        assert seq_bytes % size == 0

        stream = list((self._sample_number_to_time(seq_number + i-1),
                       d[0]) for i, d in enumerate(struct.iter_unpack(srv.byte_format,
                                                                      data[self.SEQUENCE_NUMBER_SIZE:])))
        assert len(stream) == seq_length

        # store data
        self.data[srv].extend(stream)

        log.debug("sequence: {}".format(stream))

        self.n_samples_downloaded[srv] = seq_number + seq_length - 1

        if all(self.n_samples_to_download - n == 0 for n in self.n_samples_downloaded.values()):
            self.on_download_finished()

    def _stop_download(self):
        self.StartLoggerDownload.write(0)
        self.peripheral.withDelegate(self.peripheral)
        log.info("Download finished!")

        log.info("expected samples: {}".format(self.n_samples_to_download))
        for srv, d in self.data.items():
            log.info("downloaded: {}, missed: {}".format(len(d), self.n_samples_missed[srv]))
        self._reset_download()

    def on_download_failed(self):
        self._stop_download()

    def on_download_finished(self):
        self._stop_download()

    @property
    def downloading(self):
        return self.n_samples_to_download > 0

    def progress(self):
        if self.n_samples_to_download > 0:
            return float(min(self.n_samples_downloaded.values())*100.)/self.n_samples_to_download
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

        self.Temperature = Float32Service(self.getServiceByUUID(UUID("00002234-b38d-4985-720e-0f993a68ee41")))
        self.RelativeHumidity = Float32Service(self.getServiceByUUID(UUID("00001234-b38d-4985-720e-0F993a68ee41")),
                                               unit="%")

        self.Battery = Uint8Service(self.getServiceByUUID(UUID("180F")), unit="%")

        self.Logging = LoggingService(self.getServiceByUUID(UUID("0000f234-b38d-4985-720e-0f993a68ee41")))

        self.subscribable_services = [self.Temperature, self.RelativeHumidity, self.Battery]

        self.withDelegate(self)

    def handleNotification(self, cHandle, data):
        log.debug("received data: handle={}, data={}".format(cHandle, data))
        for service in self.subscribable_services:
            if cHandle == service.getHandle():
                return service.call_listeners(data)

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
