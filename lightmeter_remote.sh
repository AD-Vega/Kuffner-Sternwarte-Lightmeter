#!/usr/bin/env bash

mypath="$(dirname $0)"

function send_mode() {
    serverport="$1"
    shift
    exec "$mypath"/lightmeter.py "$@" -f json_lines | \
        socat - TCP:"$serverport"
}

function receive_mode() {
    port="$1"
    exec socat TCP-LISTEN:"$port",reuseaddr,fork \
        SYSTEM:'exec '"'$mypath'"'/lightmeter_table.py -o lightmeter-measurements-$(TZ=UTC date -Ins).json'
}

cmd="$1"
shift
case "$cmd" in
    send) send_mode "$@" ;;
    receive) receive_mode "$@" ;;
    *)  echo "Usage: $0 send SERVER:PORT LIGHTMETER_OPTIONS"
        echo "   or: $0 receive PORT"
        exit 1
        ;;
esac
