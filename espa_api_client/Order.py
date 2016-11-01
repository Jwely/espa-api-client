import json
import os
from espa_api_client import TEMPLATE_DIR
from espa_api_client.Clients import Client


class Order(object):
    def __init__(self, template, note, enforce_note=True):
        """
        helps construct an orders json text from a template. Enforces
        the use of an order note. These order notes are used by this
        framework to prevent duplicate orders. a Client class will
        not submit an order through safe_post_order() if an active order
        already exists with the same note, and will instead return
        information about the existing order for the user to interface with.

        This is to prevent excessive ordering by accident, and generally
        promote better ordering practice.

        :param template: an OrderTemplate instance
        :param note: a note string to use for this order.
        """

        def is_empty(s):
            """ returns True if string appears to contain something """
            return not bool(s and s.strip())

        self.order_template = template
        self.order_content = template.template
        self.set_order_note(note)

        if enforce_note:
            if is_empty(self.order_content['note']):
                raise Exception("Must input a valid order note!")

    @property
    def json(self, **kwargs):
        """ json serialized order_content """
        return json.dumps(self.order_content, **kwargs)

    def set_order_note(self, note):
        self.order_content['note'] = note

    def add_tiles(self, mission, tiles):
        """ adds tiles to a missions "inputs" values """
        if mission in self.order_content.keys():
            self.order_content[mission]['inputs'] += tiles
        else:
            raise Exception("mission '{0}' is not in template!".format(mission))
        return self

    def submit(self, client=None):
        """ submit the json content of an order to an input client """
        if client is None:
            client = Client()

        if isinstance(client, Client):
            return client.safe_post_order(self.order_content)
        else:
            raise Exception("input 'client' must be an espa_api_client.Client instance")


class OrderTemplate(object):
    """ builder to create templates, save them, reuse them. The majority
    of content in an order will likely stay exactly the same over a period of time,
    the only thing that need be updated frequently are the inputs (the tiles) as
    new data becomes available.

    This class is primarily intended to load a template, add a few new tilenames to the
    'mission > inputs' property, and submit the order. At present, there isn't a good
    way to edit a template in python, its better to create a json template by referring to
    the order schema detailed at https://github.com/USGS-EROS/espa-api

     A template is a stored as a json file that looks something like this:

     {
      "olitirs8": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
        },
      "etm7": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
        },
      "tm5": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
        },
      "tm4": {
        "inputs": [],
        "products": ["sr", "sr_ndvi", "sr_savi", "sr_msavi", "cloud"]
      },
      "format": "gtiff",
      "plot_statistics": false,
      "projection": {
        "lonlat": null
      },
      "image_extents": {
        "north": 27.4,
        "south": 26.3,
        "east": -80.3,
        "west": -81.8,
        "units": "dd"
        },
      "note": ""
     }
     """

    def __init__(self, name, auto_load=True, template_dir=TEMPLATE_DIR):
        self.name = name
        self.path = os.path.join(template_dir, "{}.json".format(self.name))
        self.template = None

        if os.path.exists(self.path) and auto_load:
            self.load()

    def save(self):
        """ saves the template attribute to json """
        with open(self.path, 'w+') as f:
            f.write(json.dumps(self.template, indent=2))

    def load(self, path=None):
        """ loads template attribute from json """
        if path is None:
            path = self.path
        with open(path, 'r') as f:
            self.template = json.loads(f.read())
            print("loaded template from {0}".format(path))
            return self

    def copy_from(self, template_name):
        """ replaces the order content in this template with that from another template """
        other_template = OrderTemplate(template_name)
        self.template = other_template.load()

