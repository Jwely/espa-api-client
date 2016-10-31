import requests
import json
import os
import wget
import tarfile
from time import sleep
from datetime import datetime


API_HOST_URL = 'https://espa.cr.usgs.gov'
HEADERS = {'Content-Type': 'application/json'}


class BaseDownloader(object):

    @staticmethod
    def _download(source, dest):
        if not os.path.exists(dest):
            wget.download(url=source, out=dest)

        # now extract the targz
        extract_dest = dest.replace(".tar.gz", "")
        with tarfile.open(dest, 'r:gz') as tfile:
            tfile.extractall(extract_dest)
            print("Extracted {0}".format(extract_dest))

        # clean up temporary compressed folder
        os.remove(dest)
        return extract_dest


class LocalDownloader(BaseDownloader):

    def __init__(self, local_dir):
        self.local_dir = local_dir

    def destination_mapper(self, source):
        filename = os.path.basename(source)
        return os.path.join(self.local_dir, filename)

    def download(self, source):
        dest = self.destination_mapper(source)
        return self._download(source, dest)


class BaseClient(object):
    """
    The base client just has one to one bindings of api call types
    to each of its very simple functions. All external functions return
    simple requests response objects, use .json() method to get more human
    readable response data
    """

    def __init__(self, auth=None):
        """
        :param auth: required tuple of (username, password) strings.
        """
        if auth is None:
            username = str(input("espa username:"))
            password = str(input("espa password:"))
            self.auth = (username, password)
        else:
            self.auth = auth

        self.headers = HEADERS
        self.host = API_HOST_URL
        self.version = 'v0'         # I presume this will work for future versions
        self.verbose = False        # TODO: verbose dev flag, remove or expose

        if not self._test_auth():
            raise Exception("Failed to authenticate at https://espa.cr.usgs.gov/login")

    def _test_auth(self):
        user = self.get_user()

        if "Invalid username/password" in user.json().values():
            return False
        else:
            return True

    def _url(self, *args):
        """
        Creates api call url from args and host info, passing None's is OK.
        basically returns 'https://espa.cr.usgs.gov/api/v0/{args}'
        """
        item_list = [self.host, 'api', self.version] + list(args)
        joins = [str(item) for item in item_list if item is not None]
        url = "/".join(joins)
        if self.verbose:
            print(url)
        return url

    def _get(self, *args):
        """ wraps requests.get with url assembly from args, plus auth and header spec """
        r = requests.get(url=self._url(*args),
                         auth=self.auth,
                         headers=self.headers)
        return r

    def _post(self, *args, data=None):
        """ wraps requests.post with url assembly from args, plus auth and header spec """
        r = requests.post(url=self._url(*args),
                          auth=self.auth,
                          headers=self.headers,
                          data=data)
        return r

    def get_operations(self):
        return self._get()

    def get_user(self):
        return self._get('user')

    def get_orders_list(self, email=None):
        return self._get('list-orders', email)

    def get_order(self, order_id):
        return self._get('order', order_id)

    def get_order_status(self, order_id):
        return self._get('order-status', order_id)

    def get_order_schema(self):
        return self._get('order-schema')

    def get_item_status(self, order_num, item_num=None):
        return self._get('item-status', order_num, item_num)

    def get_available_products(self, product_id=None):
        return self._get('available-products', product_id)

    def get_projections(self):
        return self._get('projections')

    def post_order(self, order):
        if isinstance(order, dict):
            order = json.dumps(order)
        return self._post('order', data=order)


class Client(BaseClient):
    """
     The standard client class adds a few extra methods for
     filtering responses from the native API calls and expressing them
     a little more usefully.
    """
    def get_active_orders(self):
        """
        generator of orders which have not yet been purged.
        orders are stored in a list where the newest are up top, therefore once
        we hit the first purged order, every order under it will also be purged.
        """
        for order in self.get_orders_list().json()["orders"]:
            if self.get_order_status(order).json()["status"] != "purged":
                yield order
            else:
                break

    def get_items_by_status(self, order_num=None, status="complete"):
        """
        generator of items with input status
        """
        if order_num is None:
            for order in self.get_active_orders():
                yield from self.get_items_by_status(order_num=order, status=status)
        else:
            items = self.get_item_status(order_num).json()
            if "orderid" in items.keys(): # if this funciton is nested, need to parse more
                items = items["orderid"][order_num]
            if isinstance(items, list):
                for item in items:
                    if item["status"] == status:
                        yield item

    def find_order_with_note(self, search_note, active_only=True):

        if active_only:
            orders = self.get_active_orders()
        else:
            orders = self.get_orders_list().json()["orders"]

        for order_name in orders:
            note = self.get_order(order_name).json()["note"]
            if note is not None:
                if search_note in note:
                    yield order_name

    def safe_post_order(self, order, active_only=True):

        if "note" in order.keys():
            new_note = order["note"]

            orders_with_same_note = list(self.find_order_with_note(new_note, active_only))
            if len(orders_with_same_note) > 0:
                print("Found duplicate past order(s): {0}".format(orders_with_same_note))
                return {"orderid": orders_with_same_note[0]}
            else:
                return self.post_order(order).json()

    def _download_order(self, order, downloader):
        all_items = self.get_item_status(order).json()
        complete_items = list(self.get_items_by_status(order, "complete"))
        error_items = list(self.get_item_status(order, "error"))
        halted_items = complete_items + error_items
        for c in complete_items:
            if isinstance(c, dict):
                downloader.download(c["product_dload_url"])
            elif isinstance(c, requests.Request):
                downloader.download(c.json()["product_dload_url"])

        if len(halted_items) == len(all_items):
            return True
        else:
            return False

    def download_order(self, order, downloader, sleep_time=300, timeout=86400):

        complete = False
        reached_timeout = False
        starttime = datetime.now()

        while not complete and not reached_timeout:
            # wait a while before the next ping and check timeout condition
            elapsed_time = (datetime.now() - starttime).seconds
            reached_timeout = elapsed_time < timeout
            print("Elapsed time is {0}s".format(elapsed_time))

            # try to complete all downloads again
            complete = self._download_order(order, downloader)

            sleep(sleep_time)

























