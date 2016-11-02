# espa-api-client

Python interface to the [API for ordering from ESPA](https://github.com/USGS-EROS/espa-api). This API allows lots of custom processing of surface reflectance corrected data for landsat, and some other very useful science grade computations. So, this python client provides some friendly interfaces with the API to make life a little easier.

## Installation
Note, at this stage, the package is completely untested outside of py3 on Ubuntu 16. 

```
pip install espa-api-client
```
or for python3
```
pip3 install espa-api-client
```

## Example
The example below will load an order template for the DC metro area with our custom output preferences
and desired products for each mission, landsat 8 and landsat 7. That template follows the api order schema
that you can read more about at the espa-api page. It then reads the desired landsat tiles from a csv file created by
exporting search results from [Earth Explorer](http://earthexplorer.usgs.gov/), and adds them to an order created
from the template. It gives that order a unique name in the "note" field, to promote good data management practice but also
to provide a simple way of preventing duplicate orders to the ESPA API. It then submits the order, and retreives the order 
ID from the servers response. It then issues a download command on that order, that will yield completed download 
filepaths as they are available, and self terminate when all files have been either downloaded or experienced a server internal error.

One script to order, download, and process data, that need only be run once, but can be terminated and 
re-executed without issue.

```python
from espa_api_client.Clients import Client
from espa_api_client.Order import Order
from espa_api_client.OrderTemplate import OrderTemplate
from espa_api_client.parse import get_order_inputs_from_earth_explorer_export
from espa_api_client.Downloaders import EspaLandsatLocalDownloader

# build the various handlers to spec
template = OrderTemplate('example_dc_metro')
order = Order(template, note="DC-metro-20161101")
client = Client()   # will prompt user for username and password if auth argument not supplied
downloader = EspaLandsatLocalDownloader('downloads')

l8_tiles = get_order_inputs_from_earth_explorer_export('L8_export.csv')
l7_tiles = get_order_inputs_from_earth_explorer_export('L7_export.csv')
order.add_tiles("olitirs8", l8_tiles)
order.add_tiles("etm7", l7_tiles)
response = order.submit(client)

# view the servers whole response. which might indicate an ordering error!
print(response)     

# assuming there were no order submission errors
orderid = response['orderid']

# now start the downloader!
for download in client.download_order_gen(orderid, downloader):
    print(download)

    # download is a tuple with the filepath, and True if the file
    # is a fresh download.

    # this is where data pipeline scripts go that can operate
    # on files as they are downloaded (generator),

    # See the Client class for further documentation.

```

## Templates
At present, there is no helper to construct a good template. The recomended process currently requires the user
to create their own template in dictionary format, then save it (which exports it to a template json file).
```python
my_template = OrderTemplate('my_template_name')
my_template.define(my_template_dict)
my_template.save()

# subsequently it will automatically load when we use
my_template = OrderTemplate('my_template_name')

# or automatically be applied to an order with
my_order = Order('my_template_name', note='my_note')
```
To create a template, you can examine the order schema with an api request.
```python
from pprint import pprint
auth = (username, password)
my_client = Client(auth)  # authenticate client or just leave blank for prompt.
resp = my_client.get_order_schema()  # ask API about order schema
pprint(resp.json())  #print the response in readable json
```

The json template used in the example looks like this:
```json
{
    "olitirs8": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
    },
    "etm7": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
    },
    "format": "gtiff",
    "plot_statistics": false,
    "projection": {
      "lonlat": null
    },
    "image_extents": {
        "north": 39.0,
        "south": 38.7,
        "east": -76.8,
        "west": -77.2,
        "units": "dd"
    },
    "note": ""
}
```

Lets say you want a template that will work for ANY geographic area, and just download the whole surface reflectance and cloud tiles in geotiff format for whatever tiles you input. You could use a template that looks like:
```json
{
    "olitirs8": {
        "inputs": [],
        "products": ["sr", "cloud"]
    },
    "etm7": {
        "inputs": [],
        "products": ["sr", "cloud"]
    },
    "tm5": {
        "inputs": [],
        "products": ["sr", "cloud"]
    },
    "tm4": {
        "inputs": [],
        "products": ["sr", "cloud"]
    },
    "format": "gtiff",
    "plot_statistics": false,
    "projection": {
      "lonlat": null
    },
    "note": ""
}
```

## TODO:
* better docs
* Need downloader for landsat and modis to be separate, and easily selected by the client.
* Some kind of template creation assistant would be good
* Template creation assistant could also include order validation. ESPA already has their code for this made public.
* A better way to get scene identifiers than manual EE query and export. I can't believe I haven't been able to find an exposed API for this. landsat-util only works for landsat8.
