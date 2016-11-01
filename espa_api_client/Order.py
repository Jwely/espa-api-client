import json

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


