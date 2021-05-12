#!/bin/bash

# Setting up & activating virtualenv
virtualenv -p python3 .env
# shellcheck disable=SC1091
source .env/bin/activate

# Installing dependencies
pip install git+https://github.com/Fundevogel/knv-tools.git

# Creating directory structure
for dir in dist \
           imports
do
    mkdir -p "$dir"
done
