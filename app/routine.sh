#!/bin/ash
while :
do
    sleep $((CHK_INTERVAL * 60))
    curl --silent -X POST 127.0.0.1:9080
done
