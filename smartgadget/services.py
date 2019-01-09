import datetime
import logging
import struct
import time

from bluepy.btle import Characteristic as _Characteristic, Descriptor, UUID

log = logging.getLogger(__name__)


class Characteristic(_Characteristic):

    def __init__(self,
                 description_handle_offset=None,
                 unit=None,
                 byte_format=None, nbytes=1):

        self.description_handle_offset = description_handle_offset

        self.byte_format = byte_format
        self.nbytes = nbytes
        self._unit = unit

    def connect_to(self, chr: _Characteristic):
        _Characteristic.__init__(self,
                                 chr.peripheral,
                                 chr.uuid,
                                 chr.handle,
                                 chr.properties,
                                 chr.valHandle)

        if self.description_handle_offset is None:
            self._description_read = self.uuid.getCommonName
        else:
            self._description_desc = Descriptor(self.peripheral,
                                                self.uuid,
                                                self.valHandle + self.description_handle_offset)
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
                 subscription_handle_offset=1,
                 *args, **kwargs):
        Characteristic.__init__(self, *args, **kwargs)
        self.subscription_handle_offset = subscription_handle_offset
        self._listeners = []

    def connect_to(self, chr: _Characteristic):
        Characteristic.connect_to(self, chr)
        self.subscription = Descriptor(self.peripheral, self.uuid, self.valHandle + self.subscription_handle_offset)
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


class Service(object):

    def __init__(self, uuid, characteristics):
        self.service_uuid = UUID(uuid)
        self.service = None
        self.characteristics = characteristics

    def connect(self, connection):
        self.service = connection.getServiceByUUID(self.service_uuid)
        for ch, _ch in zip(self.characteristics, self.service.getCharacteristics()):
            ch.connect_to(_ch)


def add_int_to_part_of_uuid(uuid, value, part=0):
    uuid = UUID(uuid)
    parts = str(uuid).split('-')
    fmt = "{:0" + str(len(parts[part])) + "x}"
    parts[part] = fmt.format(int(parts[part], 16) + value)
    return UUID("-".join(parts))


class Uint8Service(Service, SubscribableCharacteristic):

    def __init__(self, uuid, *args, **kwargs):
        Service.__init__(self, uuid, [self])
        SubscribableCharacteristic.__init__(self,
                                            byte_format='<B',
                                            nbytes=1, *args, **kwargs)


class Float32Service(Service, SubscribableCharacteristic):

    def __init__(self, uuid, *args, **kwargs):
        Service.__init__(self, uuid, [self])
        SubscribableCharacteristic.__init__(self,
                                            description_handle_offset=1,
                                            subscription_handle_offset=2,
                                            byte_format='<f',
                                            nbytes=1, *args, **kwargs)


class LoggingService(Service):
    DOWNLOAD_TIMEOUT = 10
    SEQUENCE_NUMBER_SIZE = 4

    def __init__(self,
                 uuid,
                 subscribables,
                 *args, **kwargs):

        self.subscribables = subscribables

        self.SyncTimeMs = Characteristic(description_handle_offset=1,
                                         byte_format='<Q', *args, **kwargs)
        self.OldestTimestampMs = Characteristic(description_handle_offset=1,
                                                byte_format='<Q', *args, **kwargs)
        self.NewestTimestampMs = Characteristic(description_handle_offset=1,
                                                byte_format='<Q', *args, **kwargs)
        self.StartLoggerDownload = Characteristic(description_handle_offset=1,
                                                  byte_format='<B', *args, **kwargs)
        self.LoggerIntervalMs = Characteristic(description_handle_offset=1,
                                               byte_format='<I', *args, **kwargs)

        Service.__init__(self, uuid,
                         [
                             self.SyncTimeMs,
                             self.OldestTimestampMs,
                             self.NewestTimestampMs,
                             self.StartLoggerDownload,
                             self.LoggerIntervalMs
                         ])

        self._reset_download()

        self.data = {}
        self.n_samples_downloaded = {}
        self.n_samples_missed = {}

        self._old_delegate = None

    def _reset_download(self):
        self.missed_sequences = {}
        self.oldest_time = 0
        self.newest_time = 0
        self.interval = 0
        self.n_samples_to_download = 0

    @property
    def description(self):
        return "Logging Service"

    def start_download(self):

        log.info("initiate download....")
        self._reset_download()

        interval = self.LoggerIntervalMs.read()
        log.info("read logging interval: {0} ms".format(interval))

        self.OldestTimestampMs.write(0)
        log.info("wrote oldest timestamp: {0} ms".format(0))

        time_ms = int(time.time() * 1000.)
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
        self._old_delegate = self.service.peripheral.delegate
        self.service.peripheral.withDelegate(self)

        # create counter and data storage for all subscribed services
        subscribed_services = [src for src in self.subscribables if src.subscribed]
        self.n_samples_to_download = n_samples_to_download
        self.n_samples_downloaded = dict(zip(subscribed_services, [n_samples_to_download] * len(subscribed_services)))
        self.n_samples_missed = dict(zip(subscribed_services, [0] * len(subscribed_services)))
        self.data = {}
        for srv in subscribed_services:
            self.data[srv] = list()
            self.missed_sequences[srv] = list()

        self.StartLoggerDownload.write(1)

    def _sample_number_to_time(self, sample):
        return self.newest_time - sample * self.interval

    def handleNotification(self, cHandle, data):

        log.debug("arrived a download notification: {}".format(cHandle))
        log.debug("data length: {}".format(len(data)))

        for service in self.subscribables:
            if cHandle == service.getHandle():
                return self._process_download_data(service, data)

    def _process_download_data(self, srv: Characteristic, data):

        if len(data) <= self.SEQUENCE_NUMBER_SIZE:
            if (time.time() - self.time_start_download) >= self.DOWNLOAD_TIMEOUT:
                self.on_download_failed()
            return srv.call_listeners(data)

        seq_number = struct.unpack('<I', data[:self.SEQUENCE_NUMBER_SIZE])[0]
        log.debug("sequence {} arrived!".format(seq_number))

        log.debug("description: {}".format(srv.description))
        next_seq_number = self.n_samples_downloaded[srv] + 1

        size = struct.calcsize(srv.byte_format)
        seq_bytes = len(data) - self.SEQUENCE_NUMBER_SIZE
        seq_length = seq_bytes // size
        assert seq_bytes % size == 0

        if seq_number > next_seq_number:
            self.n_samples_missed[srv] += (seq_number - next_seq_number)
            self.missed_sequences[srv].extend(range(next_seq_number, seq_number, seq_length))
            log.debug("Download missed sequence {}! Continue with sequence {}".format(next_seq_number,
                                                                                      seq_number))
        if seq_number in self.missed_sequences[srv]:
            self.missed_sequences[srv].remove(seq_number)

        stream = list((seq_number + i - 1,
                       self._sample_number_to_time(seq_number + i - 1),
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
        self.service.peripheral.withDelegate(self._old_delegate)
        log.info("Download finished!")

        log.info("expected samples: {}".format(self.n_samples_to_download))
        for srv, d in self.data.items():
            log.info("{}: downloaded {}, missed {}".format(srv.description, len(d), self.n_samples_missed[srv]))
            log.info("missed sequences ({}) {}".format(len(self.missed_sequences[srv]) * 4,
                                                       self.missed_sequences[srv]))
        self.n_samples_to_download = 0

    def on_download_failed(self):
        self._stop_download()

    def on_download_finished(self):
        self._stop_download()

    @property
    def downloading(self):
        return self.n_samples_to_download > 0

    def progress(self):
        if self.n_samples_to_download > 0:
            return float(min(self.n_samples_downloaded.values()) * 100.) / self.n_samples_to_download
        else:
            return 0
