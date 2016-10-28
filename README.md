# espa-api-client
trying out some interface with the new espa-api

Example

```python
from parse import get_order_inputs_from_earth_explorer_export
from Client import Client, LocalDownloader

"""
An example for ordering a few tiles from landsat 7 and 8, as created
from an Earth explorer export, with some simple subsetting operations
and a geographic projection.
"""

# orde template that follows the order schema
order = {
    "olitirs8": {
        "inputs": [],   # my desired landsat 8 tiles go here
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
    },
    "etm7": {
        "inputs": [],   # desired landsat 7 tiles go here
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
    },
    "format": "gtiff",
    "plot_statistics": False,
    "projection": {"lonlat": None},  # standard geographic projection
    "image_extents": {
        "north": 39.0,
        "south": 38.7,
        "east": -76.8,
        "west": -77.2,
        "units": "dd"
    },
    "note": "20161028-DC"
}

order["olitirs8"]["inputs"] = get_order_inputs_from_earth_explorer_export("example/L8_export.csv")
order["etm7"]["inputs"] = get_order_inputs_from_earth_explorer_export("example/L7_export.csv")

# create a client and make our order
username = ""   # my username
password = ""   # my password
c = Client((username, password))
d = LocalDownloader(local_dir="example/download")
r = c.safe_post_order(order)
c.download_order(r["orderid"], downloader=d)
```
