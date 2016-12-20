#!/usr/bin/env bash
twine upload dist/*
rm -rf build
rm -rf dist
rm -rf espa_api_client.egg-info
pip3 install --upgrade espa-api-client
pip install --upgrade espa-api-client
