#!/usr/bin/env python3

import usb.core as usb
import usb.util as util
import sys
from time import sleep, time
from datetime import datetime

# The damn thing identifies as a Microchip PICDEM
lightmeterParams = {
    'idVendor': 0x04d8,
    'idProduct': 0x000c,
    'configuration': 1,
    'interface': (0, 0),
    'reqLen': 64
}

def initDevice():
    # find our device
    dev = usb.find(idVendor=lightmeterParams['idVendor'],
                   idProduct=lightmeterParams['idProduct'])

    # was it found?
    if dev is None:
        raise RuntimeError('Device not found')

    # set the active configuration. With no arguments, the first
    # configuration will be the active one
    dev.set_configuration(lightmeterParams['configuration'])

    # get an endpoint instance
    cfg = dev.get_active_configuration()
    intf = cfg[lightmeterParams['interface']]

    endpointOut = util.find_descriptor(
        intf,
        # match the first OUT endpoint
        custom_match = lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) \
            == util.ENDPOINT_OUT)

    endpointIn = util.find_descriptor(
        intf,
        # match the first IN endpoint
        custom_match = lambda e: \
            usb.util.endpoint_direction(e.bEndpointAddress) \
            == util.ENDPOINT_IN)

    if endpointOut is None or endpointIn is None:
        raise RuntimeError('Unable to open endpoints')

    return endpointIn, endpointOut

def readTemperature(endpoints):
    endpointIn, endpointOut = endpoints
    N = endpointOut.write('T')
    if N != 1:
        raise RuntimeError('USB write error')
    raw = endpointIn.read(2)
    if len(raw) != 2:
        raise RuntimeError('USB read error')
    # Throw away 3 status bits and convert to decimal.
    return (raw[0] // 8 + raw[1] * 32) / 16

def readLight(endpoints):
    endpointIn, endpointOut = endpoints
    N = endpointOut.write('L')
    if N != 1:
        raise RuntimeError('USB write error')
    raw = endpointIn.read(7)
    if len(raw) != 7:
        raise RuntimeError('USB read error')
    factors = (None, 120, 8, 4, 2, 1)
    measurementRange = raw[2]
    TslMw0 = 256 * raw[4] + raw[3];
    TslMw1 = 256 * raw[6] + raw[5];
    rawReading = 256 * raw[1] + raw[0]
    reading = rawReading * factors[measurementRange]
    isOK = rawReading < 32000
    return reading, TslMw0, TslMw1, isOK

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: {} interval_minutes".format(sys.argv[0]),
              file=sys.stderr)
        exit(1)
    minutes = float(sys.argv[1])
    endpoints = initDevice()
    while True:
        T = readTemperature(endpoints)
        L, TslMw0, TslMw1, isOK = readLight(endpoints)
        unix = int(time())
        utc = datetime.fromtimestamp(unix)
        print(utc, 'UTC', unix, 'UNIX',
              T, '°C', L, 'units',
              (('(ok' if isOK else '(err)') + ', 0x{:04x} 0x{:04x})')
              .format(TslMw0, TslMw1))
        sleep(minutes * 60)
