

# now without using pandas!
def get_order_inputs_from_earth_explorer_export(csv_path):
    """
    All the landsat record exports come with the tilename in the first column, so
    this simple function just reads it and returns that whole first column as a list.
    """
    tiles = []
    with open(csv_path, 'r') as f:
        for line in f.readlines():
            first_col = line.split(',')[0]
            if " " not in first_col:    # ignore headers by throwing out spaces
                tiles.append(first_col)
    return tiles
