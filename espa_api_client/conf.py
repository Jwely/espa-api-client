import os

LOCAL_PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_DIR = os.path.join(LOCAL_PATH, 'templates')
API_HOST_URL = 'https://espa.cr.usgs.gov'
API_VERSION = 'v0'
HEADERS = {'Content-Type': 'application/json'}

LANDSAT_TILE_REGEX = "(L)(C|O|T|E)(7|8|5|4)(\d{3})(\d{3})(\d{7})(\w{3})(\d{2})"
LANDSAT_SHORT_REGEX = "(L)(C|O|T|E)(7|8|5|4)(\d{3})(\d{3})(\d{7})"
LANDSAT_PRODUCTS = ["oli8",
                    "tm4",
                    "tm5",
                    "etm7",
                    "olitirs8"]

MODIS_TILE_REGEX = "(M)(Y|O)(D)(\d{2})(G|Q|A)(\w{1}|\d{1}).(A\d{7}).(h\d{2}v\d{2}).(\d{3}).(\d{13})"
MODIS_PRODUCTS = ["myd09gq",
                  "myd09ga",
                  "myd13q1",
                  "mod13a1",
                  "mod13a2",
                  "mod13a3",
                  "mod09a1",
                  "mod09ga",
                  "myd13a2",
                  "myd13a3",
                  "myd13a1",
                  "mod13q1",
                  "myd09q1",
                  "mod09q1",
                  "myd09a1",
                  "mod09gq"]

