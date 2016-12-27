import pandas as pd


def get_order_inputs_from_earth_explorer_export(csv_path):
    """
    All the landsat record exports come with the tilename in the first column, so
    this simple function just reads it and returns that whole first column as a list.
    """
    df = pd.read_csv(csv_path, encoding="ISO-8859-1")
    tiles = df['Landsat Scene Identifier']
    return list(tiles)
