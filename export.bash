#!/bin/bash

cd build || exit

for dir in *
do
    if [ -d "$dir" ]; then
        7z a "$dir".7z "$dir"/* -xr!*.json
    fi
done
