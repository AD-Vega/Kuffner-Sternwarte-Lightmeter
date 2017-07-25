#!/usr/bin/env python3

import usb.core as usb
import usb.util as util
import sys
import argparse
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
    try:
        dev.set_configuration(lightmeterParams['configuration'])
    except usb.USBError as e:
        # if there are permission problems, this is where they manifest
        if e.errno != 13:
            raise e
        print(e, file=sys.stderr)
        print('Set read/write permissions on device node '
              '/dev/bus/usb/{:03d}/{:03d}'.format(dev.bus,dev.address),
              file=sys.stderr)
        print('Alternatively, use udev to fix this permanently.')
        exit(1)

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

def luxFromDaysensor(Ch0, Ch1):
    """ Calculates Lux from the TAOS, www.taosinc.com TSL2560/TSL2561 two band light sensor
        for the TMB-package.
        Code from the Kuffner-Sternwarte web site.
    """
    Chr = Ch1 / Ch0
    # Apply calibration recommended by manufacturer for different channel-ratios (IR-correction for vis-sensor to get Lux)
    if Chr <= 0.50:                        Lux=0.0304  *Ch0  - 0.062*Ch0*(Ch1/Ch0)**1.4
    elif (0.50 < Chr) and (Chr  <= 0.61):  Lux=0.0224  *Ch0  - 0.031  *Ch1
    elif (0.61 < Chr) and (Chr  <= 0.80):  Lux=0.0128  *Ch0  - 0.0153 *Ch1
    elif (0.80 < Chr) and (Chr  <= 1.30):  Lux=0.00146*Ch0  - 0.00112*Ch1
    elif 1.30 < Chr:                       Lux=0
    else: raise RuntimeError("Invalid daysensor channel ratio.")
    # calibration with Voltcraft handheld vs. Lightmeter Mark 2.3 No. L001 TAOS-daysensor
    Faktor = 21.0
    return Lux*Faktor

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
    daylight = luxFromDaysensor(TslMw0, TslMw1)
    return reading, daylight, isOK

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read light level from a '
                                                 'Kuffner-Sternwarte lightmeter '
                                                 'mark 2.3')
    parser.add_argument('-i', '--interval', type=float, default=1.0,
                        help='sampling interval in minutes (can be fractional)')
    parser.add_argument('-f', '--format', default='text', choices=('text', 'json'),
                        help='output format')

    args = parser.parse_args()
    if args.format == 'text':
        print('# DATE_UTC TIME_UTC UNIX_EPOCH T_CELSIUS LIGHTMETER_COUNTS DAYLIGHT_LUX STATUS')
    elif args.format == 'json':
        import json

    endpoints = initDevice()
    while True:
        T = readTemperature(endpoints)
        L, daylight, isOK = readLight(endpoints)
        unix = int(time())
        utc = datetime.fromtimestamp(unix)
        if args.format == 'text':
            print(utc, unix, '{:.1f}'.format(T), L,
                  '{:.3g}'.format(daylight),
                  ('OK' if isOK else 'ERROR'))
        elif args.format == 'json':
            pass
        sleep(args.interval * 60)
