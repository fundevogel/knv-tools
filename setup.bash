#!/bin/bash

# Setting up & activating virtualenv
virtualenv -p python3 .env
# shellcheck disable=SC1091
source .env/bin/activate

# Installing dependencies
pip install git+https://github.com/fundevogel/knv-pypal.git
pip install -r requirements.txt

# Creating directory structure
for dir in imports \
           storage \
           build
do
    mkdir -p "$dir"
done
