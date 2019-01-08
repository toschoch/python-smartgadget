from smartgadget.scanner import SmartGadgetScanner

from pytest_mock import mocker
import mock


# Sample Test passing with nose and pytest
def test_scan(mocker):
    scanner = SmartGadgetScanner()
    mocker.patch.object(scanner,'_helper', return_value='Test')
    mocker.patch.object(scanner,'_startHelper')
    mocker.patch.object(scanner,'_stopHelper')
    mocker.patch.object(scanner,'_mgmtCmd')
    mocker.patch.object(scanner,'_writeCmd')
    mocker.patch.object(scanner,'parseResp')
    mocker.patch.object(scanner,'_waitResp')
    mocker.patch.object(scanner,'status')

    scanner.scan(3)

    scanner.status.assert_called()

    print(scanner.gadgets)
