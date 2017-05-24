from espa_api_client.Clients import Client
from espa_api_client.Order import Order
from espa_api_client.OrderTemplate import OrderTemplate
from espa_api_client.parse import get_order_inputs_from_earth_explorer_export

"""
An example for ordering a few tiles from landsat 7 and 8, as created
from an Earth explorer export and a predefined order template, which follows
the schema described at the espa-api host repo: https://github.com/USGS-EROS/espa-api

This script uses an order note, which only allows the order to be submitted if another
order with the same note is not already associated with the account. This prevents duplicate
ordering, and also allows the same ordering code to simply be run again at a later time
to download the order products if the script is halted.
"""


def main():
    template = OrderTemplate('example_dc_metro')
    order = Order(template, note="DC-metro-20170524-trash")
    client = Client()

    l8_tiles = get_order_inputs_from_earth_explorer_export('L8_export.csv')
    # l7_tiles = get_order_inputs_from_earth_explorer_export('L7_export.csv')
    # myd13a1_tiles = get_order_inputs_from_earth_explorer_export('MYD13A1_export.csv')
    order.add_tiles("olitirs8", l8_tiles)
    # order.add_tiles("etm7", l7_tiles)
    # order.add_tiles("olitirs8", ["LC80150332300024LGN00"])  # example of a bad tile addition
    # order.add_tiles("myd13a1", myd13a1_tiles)
    response = order.submit(client)
    print(response)

    orderid = response['orderid']
    downloads = client.download_order_gen(order_id=orderid)
    for download in downloads:
        print(download)
        # download is a tuple with the filepath, and True if the file
        # is a fresh download.

        # this is where data pipeline scripts go that can operate
        # on files as they are downloaded (generator),

        # See the Client class for further documentation.

if __name__ == "__main__":
    main()
