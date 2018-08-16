from bluepy import btle


if __name__ == '__main__':

    sc = btle.Scanner(iface=0)

    for dv in sc.scan(timeout=10):
        dv = btle.ScanEntry()
        dv.getScanData()


    dev = btle.Peripheral(addrType=btle.ADDR_TYPE_RANDOM)

    dev
