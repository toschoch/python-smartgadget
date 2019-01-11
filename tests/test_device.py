import binascii

from bluepy.btle import ADDR_TYPE_RANDOM

from smartgadget.device import SmartGadget

from test_scanner import Responses


# # Sample Test passing with nose and pytest
# def test_connect(mocker):
#
#     dev = SmartGadget('e2:07:bc:53:40:61')
#
#     mocker.patch.object(dev.peripheral, '_helper', return_value='Test')
#     mocker.patch.object(dev.peripheral, '_startHelper')
#     mocker.patch.object(dev.peripheral, '_stopHelper')
#     mocker.patch.object(dev.peripheral, '_mgmtCmd')
#     mocker.patch.object(dev.peripheral, '_writeCmd')
#     mocker.patch.object(dev.peripheral, 'parseResp')
#     mocker.patch.object(dev.peripheral, 'status')
#
#     responses = {1: {'code': ['success']},
#                  2: {'rsp': ['scan'],
#                      'addr': [binascii.unhexlify("e207bc534061")],
#                      'type': [ADDR_TYPE_RANDOM],
#                      'rssi': [76],
#                      'flag': [0],
#                      'code': ['success'],
#                      'd': [b'\x02\x01\x06\x11\tSmart Humigadget']},
#                  3: {'rsp': ['scan'],
#                      'addr': [binascii.unhexlify("f207bc536061")],
#                      'type': [ADDR_TYPE_RANDOM],
#                      'rssi': [87],
#                      'flag': [0],
#                      'code': ['success']}}
#
#     mocker.patch.object(dev.peripheral, '_waitResp', side_effect=Responses(responses))
#
#     dev.connect()
