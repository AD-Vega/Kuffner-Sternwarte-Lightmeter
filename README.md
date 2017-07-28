# Kuffner-Sternwarte-Lightmeter

Alternative driver for the Kuffner-Sternwarte Lightmeter Mark 2.3, written in
Python. More information on the hardware can be found at [the
Kuffner-Sternwarte
wiki](http://kuffner-sternwarte.at/hms/wiki/index.php5?title=Lightmeter). This
driver requires pyusb and works similarly to the original driver which it is
based on, but provides more versatile output. In particular, it provides
several variants of JSON formatting which makes it easy to store data portably
or send it over a network. For storage, the data is formatted according to the
[`table-schema`](https://specs.frictionlessdata.io/table-schema/), which is also
used by [`pandas`](http://pandas.pydata.org/). A utility for importing the
tabular data into a `pandas` `DataFrame` is provided.

## Dependencies

  - `python3`
  - `pyusb` for device access
  - `pandas` for easy data import
  - `socat` for the remote logging example

## Usage

To simply print sensor readings every two minutes, run

    $ ./lightmeter.py -i 2
    # DATE_UTC TIME_UTC UNIX_EPOCH T_CELSIUS LIGHTMETER_COUNTS DAYLIGHT_LUX STATUS
    2017-07-26 14:49:09.459977+00:00 1501080549 26.7 1523160 72.4 OK
    2017-07-26 14:51:09.598521+00:00 1501080669 26.6 1520880 71.7 OK
    2017-07-26 14:53:09.686995+00:00 1501080789 26.6 1519440 70.2 OK

Use `Ctrl+C` to interrupt. The default output is plain text with
space-delimited columns. The comment that is printed first labels the columns.
Temperature is in degrees Celsius and the daylight sensor readings (if your
hardware has one) are in Lux. The main sensor readings are in raw counts
because calibration is necessary (see the lightmeter's
[webpage](http://kuffner-sternwarte.at/hms/wiki/index.php5?title=Lightmeter_calibration)).

A slightly less readable output that is easier to work with is JSON. Running

    $ ./lightmeter.py -i 2 -f json_table > myreadings.json

generates a file can be parsed with any software that can read JSON and
contains all the information needed to interpret the records. If you use
`python` to process the data, a function is provided in `lightmeter_pandas.py`
to easily import the data, e.g.

    $ python
    Python 3.6.1 (default, Mar 27 2017, 00:27:06)
    [GCC 6.3.1 20170306] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> import lightmeter_pandas
    >>> readings = lightmeter_pandas.from_json('myreadings.json')
    >>> print(readings)
                                      T        L   D     S
    TS
    2017-07-26 14:36:19.372882  26.8125  1531200  79  True
    2017-07-26 14:36:21.234798  26.8125  1530120  79  True
    2017-07-26 14:36:23.090475  26.8125  1530840  79  True
    2017-07-26 14:36:24.953951  26.7500  1530120  79  True
    2017-07-26 14:36:26.818038  26.8125  1529760  79  True
    2017-07-26 14:36:28.674192  26.8125  1529760  79  True
    2017-07-26 14:36:30.530111  26.8125  1530240  79  True
    2017-07-26 14:36:32.386035  26.7500  1530240  79  True
    2017-07-26 14:36:34.249958  26.8125  1529880  79  True
    >>>

There is another format called `json_lines` which does not contain a schema,
but consists only of newline-delimited records. Because the records are
standalone, they can be sent through a network (e.g. using `socat` or
`netcat`). These records can be converted into `json_table` format by piping
them through `lightmeter_table.py`.

An example script is provided that stores data on a remote server. To use it,
run the following on the machine that will store data

    $ ./lightmeter_remote.sh receive 1234

and the following on the machine with the lightmeter

    $ ./lightmeter_remote.sh send remotemachineaddress:1234 -i 2

where 1234 is an available port. Other options can be added to the sending
command, except for the data format. On the receiving end, a file will be
generated with a timestamped name and measurements will be stored as
`json_table`. The receiver opens a new file for each connection and can even
handle multiple senders.

## Authors

This software is written and maintained by [Jure
Varlec](mailto:jure.varlec@ad-vega.si) and Astronomical Society Vega —
Ljubljana. It is licenced under the GNU General Public Licence, version 3 or
later.
