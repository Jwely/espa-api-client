import os

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(LOCAL_PATH, 'templates')
API_HOST_URL = 'https://espa.cr.usgs.gov'
API_VERSION = 'v0'
HEADERS = {'Content-Type': 'application/json'}