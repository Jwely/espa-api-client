import requests
import simplejson as json
from simplejson.scanner import JSONDecodeError
from time import sleep
from datetime import datetime
from espa_api_client.conf import API_HOST_URL, API_VERSION, HEADERS
from espa_api_client.Exceptions import AuthError


class ServiceOfflineError(Exception):
    pass


class BaseClient(object):
    """
    The base client just has one to one bindings of api call types
    to each of its very simple functions. All external functions return
    simple requests response objects, use .json() method to get more human
    readable response data
    """

    def __init__(self, auth=None):
        """
        :param auth: tuple of (username, password) strings.
        """
        if auth is None:
            username = str(input("espa username:"))
            password = str(input("espa password:"))
            self.auth = (username, password)
        else:
            self.auth = auth

        self.headers = HEADERS
        self.host = API_HOST_URL
        self.version = API_VERSION
        self.verbose = False  # TODO: verbose dev flag, remove or expose

        if not self._test_auth():
            raise AuthError("Failed to authenticate at https://espa.cr.usgs.gov/login")

    def _test_auth(self):
        """ checks that authentication info works """
        user = self.get_user()
        try:
            if "Invalid username/password" in user.json().values():
                return False
            else:
                return True
        except JSONDecodeError:
            raise ServiceOfflineError("{}".format(user))

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

    def post_order(self, order_content):
        if isinstance(order_content, dict):
            order_content = json.dumps(order_content)
        return self._post('order', data=order_content)


class Client(BaseClient):
    """
     The standard client class adds a few extra methods for
     filtering responses from the native API calls and expressing them
     a little more usefully.
    """
    def __init__(self, auth=None):
        super(Client, self).__init__(auth)
        self.schema = self.get_order_schema().json()

    def available_sensors(self):
        """ lists available sensors from the order schema """
        return sorted(self.schema["oneormoreobjects"])

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

    def get_items_by_status(self, order_id=None, status="complete"):
        """
        generator of items with input status. Common status responses
        are ['complete', 'error', 'queued', 'processing', 'cached'].
        """
        if order_id is None:
            for order_id in self.get_active_orders():
                yield from self.get_items_by_status(order_id=order_id, status=status)
        else:
            items = self.get_item_status(order_id).json()
            if "orderid" in items.keys():  # if this funciton is nested, need to parse more
                items = items["orderid"][order_id]
            if isinstance(items, list):
                for item in items:
                    if item["status"] == status:
                        yield item

    def list_order_notes(self, active_only=True, verbose=False):
        """
        Returns a list of tuples, where the first element of the tuple
        is the order name, and the second element is the note used for that
        order
        """
        if active_only:
            order_names = self.get_active_orders()
        else:
            order_names = self.get_orders_list().json()["orders"]

        order_notes = [(o, self.get_order(o).json()['note']) for o in order_names]
        if verbose:
            if active_only:
                print("Active Orders / Notes")
            else:
                print("Orders / Notes")
            for o, n in order_notes:
                print(o, '\t', n)

        return order_notes

    def find_orders_with_note(self, search_note, active_only=True):
        """
        Finds an order with a note which CONTAINS the search note. An
        input note of "my-order" will return an order with note
        "my-order-2016-01-01".

        not sure if this behavior is desired or not.
        """
        return_list = []
        order_notes = self.list_order_notes(active_only=active_only)
        for order_name, note in order_notes:
            if note:
                if search_note in note:
                    return_list.append(order_name)
        return return_list

    def safe_post_order(self, order_id, active_only=True):
        """12222
        exactly as .post_order() of the parent class, but will first
        check for existing orders with a common 'note' field. If one or more
        are found, function returns a response that looks like a fresh
        order response, but with the already existing order ID.
        """
        if "note" in order_id.keys():
            new_note = order_id["note"]

            orders_with_same_note = self.find_orders_with_note(new_note, active_only)
            if len(orders_with_same_note) > 0:
                print("Found duplicate past order(s): {0}".format(orders_with_same_note))
                print("Returning {0}".format({"orderid": orders_with_same_note[0]}))
                return {"orderid": orders_with_same_note[0]}
            else:
                return self.post_order(order_id).json()

    def _error_items(self, order, verbose=False):
        """ returns list of items with status 'error', can print summary. """
        error_items = list(self.get_item_status(order, "error"))
        if verbose:
            if len(error_items) > 0:
                print("Fatal Error items ({0})".format(len(error_items)))
                for item in error_items:
                    print('\t', item["name"], item["note"])
        return error_items

    def _active_items(self, order_id, verbose=False):
        """
        returns list of items with active statuses, (not complete or error).
        can print summary if verbose is True.
        """
        all_items = self.get_item_status(order_id).json()["orderid"][order_id]
        active_items = [item for item in all_items
                        if item['status'] != 'complete' and item['status'] != 'error']
        if verbose:
            if len(active_items) > 0:
                print("Active items ({0})".format(len(active_items)))
                for item in active_items:
                    print('\t', item["name"], item["status"])
        return active_items

    def _complete_items(self, order, verbose=False):
        """
        checks order for completed items (ready for download) and then returns
        a list of completed items
        """
        complete_items = list(self.get_items_by_status(order, "complete"))
        if verbose:
            if len(complete_items) > 0:
                print("Completed items ({0})".format(len(complete_items)))
                for item in complete_items:
                    print('\t', item["name"], item["completion_date"])
        return complete_items

    # TODO: some check to ensure input downloader is appropriate for each filet ype.
    def download_order_gen(self, order_id, downloader, sleep_time=300, timeout=86400, **dlkwargs):
        """
        This function is a generator that yields the results from the input downloader classes
        download() method. This is a generator mostly so that data pipeline functions that operate
        upon freshly downloaded files may immediately get started on them.

        :param order_id:               order name
        :param downloader:          instance of a Downloaders.BaseDownloader or child class
        :param sleep_time:          number of seconds to wait between checking order status
        :param timeout:             maximum number of seconds to run program
        :param dlkwargs:            keyword arguments for downloader.download() method.
        :returns:                   yields values from the input downloader.download() method.
        """
        complete = False
        reached_timeout = False
        starttime = datetime.now()

        while not complete and not reached_timeout:
            # wait a while before the next ping and check timeout condition
            elapsed_time = (datetime.now() - starttime).seconds
            reached_timeout = elapsed_time > timeout
            print("Elapsed time is {0}m".format(elapsed_time / 60.0))

            # check order completion status, and list all items which ARE complete
            complete_items = self._complete_items(order_id, verbose=False)

            for c in complete_items:
                if isinstance(c, dict):
                    url = c["product_dload_url"]
                    yield downloader.download(url, **dlkwargs)
                elif isinstance(c, requests.Request):
                    url = c.json()["product_dload_url"]
                    yield downloader.download(url, **dlkwargs)
                else:
                    raise Exception("Could not interpret {0}".format(c))

            def is_complete():
                return len(self._active_items(order_id, verbose=True)) < 1

            # check for completeness and break or wait.
            complete = is_complete()
            if complete:
                break
            sleep(sleep_time)
