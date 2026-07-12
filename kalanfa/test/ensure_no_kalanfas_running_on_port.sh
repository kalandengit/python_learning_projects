#!/bin/bash

echo "Checking for processes running on $1/tcp..."
running_kalanfas=`lsof -i -P -U | grep $1 | grep kalanfa`
echo $running_kalanfas

if [ `lsof -i -P -U | grep $1 | grep kalanfa | grep LISTEN | grep -c '^'` -gt "0" ]; then
    # looks like kalanfa is running!
    exit 1
else
    exit 0
fi
