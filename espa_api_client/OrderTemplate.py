import json
import os

from espa_api_client.conf import TEMPLATE_DIR


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
        """
        Creates an order template instance. If input name already exists and
        auto_load is True, it will check for file '{name}.json' in the template_dir
        and load its contents if available. To create new order templates,
        :param name: (str) name for this template! (should be a valid filename)
        :param auto_load: check template_dir for templates with this name
        :param template_dir: folder where templates are stored.
        """
        self.name = name
        self.path = os.path.join(template_dir, "{}.json".format(self.name))
        self.template_content = dict()

        if os.path.exists(self.path) and auto_load:
            self.load()

    def define(self, template_dict):
        """ allows input of template dictionary """
        self.template_content.update(template_dict)
        self.save()
        return self

    def save(self, path=None):
        """ saves the template attribute to json. dumps to template_dir if no path is supplied """
        if path is None:
            path = self.path

        with open(path, 'w+') as f:
            f.write(json.dumps(self.template_content, indent=2))
        print("Template saved to {0}".format(path))
        return self

    def load(self, path=None):
        """ loads template attribute from json. checks template_dir for file if no path is supplied """
        if path is None:
            path = self.path
        with open(path, 'r') as f:
            self.template_content = json.loads(f.read())
            print("loaded template from {0}".format(path))
        return self

    def copy_from(self, template_name):
        """ replaces the order content in this template with that from another template """
        other_template = OrderTemplate(template_name)
        self.template_content = other_template.load().template_content
        return self
