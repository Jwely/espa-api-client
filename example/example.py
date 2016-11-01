from espa_api_client.Clients import Client
from espa_api_client.Order import Order
from espa_api_client.OrderTemplate import OrderTemplate
from espa_api_client.parse import get_order_inputs_from_earth_explorer_export
from espa_api_client.Downloaders import EspaLandsatLocalDownloader

"""
An example for ordering a few tiles from landsat 7 and 8, as created
from an Earth explorer export and a predefined order template, which follows
the schema described at the espa-api host repo: https://github.com/USGS-EROS/espa-api

This script uses an order note, which only allows the order to be submitted if another
order with the same note is not already associated with the account. This prevents duplicate
ordering, and also allows the same ordering code to simply be run again at a later time
to download the order products if the script is halted.

The
"""


def main():
    template = OrderTemplate('dc_metro')
    order = Order(template, note="DC-metro-20161101")
    client = Client()
    downloader = EspaLandsatLocalDownloader('downloads')

    l8_tiles = get_order_inputs_from_earth_explorer_export('L8_export.csv')
    l7_tiles = get_order_inputs_from_earth_explorer_export('L7_export.csv')
    order.add_tiles("olitirs8", l8_tiles)
    order.add_tiles("etm7", l7_tiles)
    orderid = order.submit(client)['orderid']
    for download in client.download_order_gen(orderid, downloader):
        print(download)
        # this is where data pipeline scripts go that can operate
        # on files as they are downloaded (generator)

if __name__ == "__main__":
    main()

