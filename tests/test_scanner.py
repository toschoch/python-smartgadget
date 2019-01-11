import binascii

from bluepy.btle import ADDR_TYPE_RANDOM

from smartgadget.device import SmartGadget
from smartgadget.scanner import SmartGadgetScanner


class Responses(object):

    def __init__(self, responses: dict):
        self._calls = 0
        self.responses = responses

    def __call__(self, *args, **kwargs):
        self._calls += 1

        for i, resp in self.responses.items():
            if self._calls == i:
                return resp

        return None


# Sample Test passing with nose and pytest
def test_scan(mocker):
    scanner = SmartGadgetScanner()

    mocker.patch.object(scanner, '_helper', return_value='Test')
    mocker.patch.object(scanner, '_startHelper')
    mocker.patch.object(scanner, '_stopHelper')
    mocker.patch.object(scanner, '_mgmtCmd')
    mocker.patch.object(scanner, '_writeCmd')
    mocker.patch.object(scanner, 'parseResp')
    mocker.patch.object(scanner, 'status')

    responses = {1: {'code': ['success']},
                 2: {'rsp': ['scan'],
                     'addr': [binascii.unhexlify("e207bc534061")],
                     'type': [ADDR_TYPE_RANDOM],
                     'rssi': [76],
                     'flag': [0],
                     'code': ['success'],
                     'd': [b'\x02\x01\x06\x11\tSmart Humigadget']},
                 3: {'rsp': ['scan'],
                     'addr': [binascii.unhexlify("f207bc536061")],
                     'type': [ADDR_TYPE_RANDOM],
                     'rssi': [87],
                     'flag': [0],
                     'code': ['success']}}

    mocker.patch.object(scanner, '_waitResp', side_effect=Responses(responses))

    scanner.scan(3)

    assert len(scanner.scanned) == 2

    assert len(scanner.gadgets) == 1

    for addr, dev in scanner.gadgets.items():
        assert addr == 'e2:07:bc:53:40:61'
        assert isinstance(dev, SmartGadget)

# def test_scan_real():
#     from bluepy.btle import DefaultDelegate, Scanner
#     from smartgadget.scanner import is_smartgadget
#
#     class MyDelegate(DefaultDelegate):
#         def handleDiscovery(self, scanEntry, isNewDev, isNewData):
#             if isNewDev and is_smartgadget(scanEntry):
#                 print("found smartgadget")
#
#     sc = Scanner().withDelegate(MyDelegate())
#     sc.scan(10)
