import logging
import datetime
from apscheduler.schedulers.background import BlockingScheduler
from apscheduler.executors.pool import ProcessPoolExecutor, ThreadPoolExecutor

from smartgadgetmqtt.device import SmartGadget
from smartgadgetmqtt.scanner import SmartGadgetScanner

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(levelname)s | %(message)s')

if __name__ == '__main__':

    scheduler = BlockingScheduler(
        executors={
            'default': ThreadPoolExecutor(5),
            'process': ProcessPoolExecutor(max_workers=1)})

    class AppendSmartGadget(SmartGadgetScanner):

        def __init__(self, gadgets={}, jobs={}):
            SmartGadgetScanner.__init__(self, gadgets)
            self.jobs = jobs

        def on_appearance(self, dev: SmartGadget):
            logging.info("appearance {}".format(dev))

            if dev.addr not in self.jobs:
                logging.info("add download for {}".format(dev))
                job = scheduler.add_job(AppendSmartGadget.download,
                                        'interval',
                                        args=(dev,),
                                        hours=4,
                                        coalesce=True,
                                        start_date=datetime.datetime.now() + datetime.timedelta(seconds=1),
                                        executor='process',
                                        misfire_grace_time=120)
                self.jobs[dev.addr] = job

            else:
                logging.info("resume download for {}".format(dev))
                self.jobs[dev.addr].resume()

        def on_disappearance(self, dev: SmartGadget):
            logging.info("pause download for {}".format(dev))
            self.jobs[dev.addr].pause()

        @staticmethod
        def download(dev: SmartGadget):
            dev.connect()
            logging.info("{}, Battery: {:02d}%".format(dev, dev.Battery.read()))
            logging.info("{}".format(dev.download_temperature_and_relative_humidity()))
            dev.disconnect()


    scanner = AppendSmartGadget()

    scheduler.add_job(scanner.scan, 'interval', minutes=5, args=(10,),
                      start_date=datetime.datetime.now()+datetime.timedelta(seconds=1))

    scheduler.start()

    # scanner = SmartGadgetScanner()
    # scanner.scan(3)
    #
    # g = list(scanner.gadgets.values())[0]
    # g.connect()
    # g.download_temperature_and_relative_humidity()