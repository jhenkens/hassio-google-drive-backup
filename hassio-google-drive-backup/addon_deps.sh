#!/bin/bash

apk add python3 fping linux-headers libc-dev libffi-dev python3-dev gcc py3-pip
pip3 install --upgrade pip wheel setuptools

# Create virtual environment
python3 -m venv /app/venv

# Install requirements in venv
/app/venv/bin/pip install --upgrade pip wheel setuptools
/app/venv/bin/pip install --trusted-host pypi.python.org -r requirements-addon.txt

# Remove packages we only needed for installation
apk del linux-headers libc-dev libffi-dev python3-dev gcc