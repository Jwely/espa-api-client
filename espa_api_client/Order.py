import json

from espa_api_client.OrderTemplate import OrderTemplate
from espa_api_client.Clients import Client
from espa_api_client.Exceptions import InvalidOrderNote, \
    EmptyOrderTemplate, InvalidClient


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

        :param template: an OrderTemplate instance or (str) name of saved template
        :param note: a note string to use for this order.
        :param enforce_note: forces input of a non-empty note string.
        """

        def is_empty(s):
            """ returns True if string appears to contain something """
            return not bool(s and s.strip())

        self.template = self._set_template(template)
        self.order_content = template.template_content
        self.set_order_note(note)

        if enforce_note:
            if is_empty(self.order_content['note']):
                raise InvalidOrderNote("Must input a valid order note!")

    @staticmethod
    def _set_template(template):
        """
        Validates 'template' __init__ input. Allows input of saved template name instead
        of a OrderTemplate instance, but verifies the template exists and has defined content
        before accepting it.
        """
        if isinstance(template, OrderTemplate):
            return template
        elif isinstance(template, str):
            ot = OrderTemplate(template)
            if ot.template_content:  # accept string input if template exists and isn't empty!
                return ot
            else:
                raise EmptyOrderTemplate(
                    "Template with name '{0}' is empty or not found!".format(template))
        else:
            raise EmptyOrderTemplate(
                "Could not interpret template input of type '{0}'".format(type(template)))

    @property
    def json(self, **kwargs):
        """ json serialized order_content """
        return json.dumps(self.order_content, **kwargs)

    def set_order_note(self, note):
        """ sets 'note' property of the order """
        self.order_content['note'] = note

    def add_tiles(self, mission, tiles):
        """ adds tiles to a missions "inputs" values """
        if mission in self.order_content.keys():
            self.order_content[mission]['inputs'] += tiles
        else:
            raise Exception("mission '{0}' is not in template!".format(mission))
        return self

    def remove_tiles(self, mission, tiles):
        """ removes tiles from missions "inputs" values """
        if mission in self.order_content.keys():
            for tile in tiles:
                if tile in self.order_content[mission]['inputs']:
                    self.order_content[mission]['inputs'].remove(tile)

    def submit(self, client=None):
        """ submit the content of an order to an input Client instance. """

        # the api rejects product specs with no inputs listed, so remove them before submitting.
        remove_list = []
        for top_level in self.order_content.keys():
            if isinstance(self.order_content[top_level], dict):
                if 'inputs' in self.order_content[top_level].keys():
                    if not self.order_content[top_level]['inputs']:
                        remove_list.append(top_level)
        for rem in remove_list:
            del self.order_content[rem]

        if client is None:
            client = Client()

        if isinstance(client, Client):
            return client.safe_post_order(self.order_content)
        else:
            raise InvalidClient("input 'client' must be an espa_api_client.Client instance")


