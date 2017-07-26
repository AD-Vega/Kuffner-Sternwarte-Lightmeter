#!/usr/bin/env python3

import sys
import atexit
import argparse

# PANDAS compatible JSON table-schema
# https://specs.frictionlessdata.io/table-schema/
jsonSchemaPrefix = """\
{"schema": {
    "primaryKey": ["TS"],
    "fields": [
        {"name": "TS",
         "type": "datetime",
         "title": "Timestamp",
         "description": "ISO8601 string, UTC"},
        {"name": "T",
         "type": "number",
         "title": "Temperature",
         "description": "Temperature in degrees Celsius"},
        {"name": "L",
         "type": "integer",
         "title": "Light level",
         "description": "Light level counts, no calibration"},
        {"name": "D",
         "type": "integer",
         "title": "Daylight",
         "description": "Daylight sensor reading in Lux"},
        {"name": "S",
         "type": "boolean",
         "title": "Status",
         "description": "True if everything is OK, false otherwise"}
    ]
 },
 "data": ["""

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Convert json_line or '
                                     'json_line_long format into json_table. '
                                     'Useful for sending the output of '
                                     'lightmeter.py over the network and '
                                     'storing it on the other side.')
    parser.parse_args()

    longNames = ('utc', 'temperature', 'lightlevel', 'daylight', 'status')
    shortNames = ('TS', 'T', 'L', 'D', 'S')
    print(jsonSchemaPrefix, end='')
    printComma = ''

    @atexit.register
    def finish():
        print('\n]}')

    while True:
        line = sys.stdin.readline()
        if line == '':
            break
        if 'lightlevel' in line:
            # long format json
            for long, short in zip(longNames, shortNames):
                line = line.replace(long, short)
        line = line.rstrip()
        print(printComma, line, end='', sep='\n', flush=True)
        printComma = ','
