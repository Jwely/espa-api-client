import pandas as pd
import re
import json
from espa_api_client.conf import LANDSAT_TILE_REGEX, LANDSAT_SHORT_REGEX, MODIS_TILE_REGEX


def get_order_inputs_from_earth_explorer_export(csv_path):
    """
    All the landsat record exports come with the tilename in the first column, so
    this simple function just reads it and returns that whole first column as a list.
    """
    df = pd.read_csv(csv_path, encoding="ISO-8859-1")
    tiles = []
    # check for landsat tiles
    if 'Landsat Scene Identifier' in df.columns.values:
        tiles += [t for t in list(df['Landsat Scene Identifier']) if t]
    if 'Local Granule ID' in df.columns.values:
        tiles += [t.replace(".hdf", "") for t in list(df['Local Granule ID']) if t]
    return tiles


def search_landsat_tiles(string, short=False):
    """ searches string for landsat tiles and returns list of any found """
    if short:
        regex = LANDSAT_SHORT_REGEX
    else:
        regex = LANDSAT_TILE_REGEX
    tiles = re.findall(regex.lower(), string.lower())
    if tiles:
        tiles = [''.join(chunks).upper() for chunks in tiles]
    return list(set(tiles))


def search_modis_tiles(string):
    """ searches string for modis tiles and returns list of any found """
    tiles = re.findall(MODIS_TILE_REGEX.lower(), string.lower())
    if tiles:
        tiles = [''.join(chunks).upper() for chunks in tiles]
    return list(set(tiles))
