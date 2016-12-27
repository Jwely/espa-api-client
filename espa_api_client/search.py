# Most of this code was selectively copied from developmentseed/landsat-util
# https://github.com/developmentseed/landsat-util
# Minor modifications by Jwely@Github

import json
import time
import requests
import geocoder
import re


API_URL = 'https://api.developmentseed.org/landsat'

# Geocoding confidence scores,
# from https://github.com/DenisCarriere/geocoder/blob/master/docs/features/Confidence%20Score.md
geocode_confidences = {
    10: 0.25,
    9: 0.5,
    8: 1.,
    7: 5.,
    6: 7.5,
    5: 10.,
    4: 15.,
    3: 20.,
    2: 25.,
    1: 99999.,
    # 0: unable to locate at all
}


def geocode(address, required_precision_km=1.):
    """ Identifies the coordinates of an address
    :param address:
        the address to be geocoded
    :type value:
        String
    :param required_precision_km:
        the maximum permissible geographic uncertainty for the geocoding
    :type required_precision_km:
        float
    :returns:
        dict
    """
    geocoded = geocoder.google(address)
    precision_km = geocode_confidences[geocoded.confidence]

    if precision_km <= required_precision_km:
        (lon, lat) = geocoded.geometry['coordinates']
        return {'lat': lat, 'lon': lon}
    else:
        raise ValueError("Address could not be precisely located")


def three_digit(number):
    """ Add 0s to inputs that their length is less than 3.
    :param number:
        The number to convert
    :type number:
        int
    :returns:
        String
    """
    number = str(number)
    if len(number) == 1:
        return u'00%s' % number
    elif len(number) == 2:
        return u'0%s' % number
    else:
        return number


def create_paired_list(value):
    """ Create a list of paired items from a string.
    :param value:
        the format must be 003,003,004,004 (commas with no space)
    :type value:
        String
    :returns:
        List
    :example:
        create_paired_list('003,003,004,004')
        [['003','003'], ['004', '004']]
    """

    if isinstance(value, list):
        value = ",".join(value)

    array = re.split('\D+', value)

    # Make sure the elements in the list are even and pairable
    if len(array) % 2 == 0:
        new_array = [list(array[i:i + 2]) for i in range(0, len(array), 2)]
        return new_array
    else:
        raise ValueError('The string should include pairs and be formated. '
                         'The format must be 003,003,004,004 (commas with '
                         'no space)')


class Search(object):
    """ The search class """

    def __init__(self):
        self.api_url = API_URL

    def search(self, paths_rows=None, lat=None, lon=None, address=None, start_date=None, end_date=None, cloud_min=None,
               cloud_max=None, limit=1, geojson=False):
        """
        The main method of Search class. It searches Development Seed's Landsat API.
        :param paths_rows:
            A string in this format: "003,003,004,004". Must be in pairs and separated by comma.
        :type paths_rows:
            String
        :param lat:
            The latitude
        :type lat:
            String, float, integer
        :param lon:
            The The longitude
        :type lon:
            String, float, integer
        :param address:
            The address
        :type address:
            String
        :param start_date:
            Date string. format: YYYY-MM-DD
        :type start_date:
            String
        :param end_date:
            date string. format: YYYY-MM-DD
        :type end_date:
            String
        :param cloud_min:
            float specifying the minimum percentage. e.g. 4.3
        :type cloud_min:
            float
        :param cloud_max:
            float specifying the maximum percentage. e.g. 78.9
        :type cloud_max:
            float
        :param limit:
            integer specifying the maximum results return.
        :type limit:
            integer
        :param geojson:
            boolean specifying whether to return a geojson object
        :type geojson:
            boolean
        :returns:
            dict
        :example:
            s = Search()
            s.search('003,003', '2014-01-01', '2014-06-01')
            {
                'status': u'SUCCESS',
                'total_returned': 1,
                'total': 1,
                'limit': 1
                'results': [
                    {
                        'sat_type': u'L8',
                        'sceneID': u'LC80030032014142LGN00',
                        'date': u'2014-05-22',
                        'path': u'003',
                        'thumbnail': u'http://....../landsat_8/2014/003/003/LC80030032014142LGN00.jpg',
                        'cloud': 33.36,
                        'row': u'003
                    }
                ]
            }
        """

        search_string = self.query_builder(paths_rows, lat, lon, address, start_date, end_date, cloud_min, cloud_max)

        # Have to manually build the URI to bypass requests URI encoding
        # The api server doesn't accept encoded URIs

        r = requests.get('%s?search=%s&limit=%s' % (self.api_url, search_string, limit))

        r_dict = json.loads(r.text)
        result = {}

        if 'error' in r_dict:
            result['status'] = u'error'
            result['code'] = r_dict['error']['code']
            result['message'] = r_dict['error']['message']

        elif 'meta' in r_dict:
            if geojson:
                result = {
                    'type': 'FeatureCollection',
                    'features': []
                }
                for r in r_dict['results']:
                    feature = {
                        'type': 'Feature',
                        'properties': {
                            'sceneID': r['sceneID'],
                            'row': three_digit(r['row']),
                            'path': three_digit(r['path']),
                            'thumbnail': r['browseURL'],
                            'date': r['acquisitionDate'],
                            'cloud': r['cloudCoverFull']
                        },
                        'geometry': {
                            'type': 'Polygon',
                            'coordinates': [
                                [
                                    [r['upperLeftCornerLongitude'], r['upperLeftCornerLatitude']],
                                    [r['lowerLeftCornerLongitude'], r['lowerLeftCornerLatitude']],
                                    [r['lowerRightCornerLongitude'], r['lowerRightCornerLatitude']],
                                    [r['upperRightCornerLongitude'], r['upperRightCornerLatitude']],
                                    [r['upperLeftCornerLongitude'], r['upperLeftCornerLatitude']]
                                ]
                            ]
                        }
                    }

                    result['features'].append(feature)

            else:
                result['status'] = u'SUCCESS'
                result['total'] = r_dict['meta']['results']['total']
                result['limit'] = r_dict['meta']['results']['limit']
                result['total_returned'] = len(r_dict['results'])
                result['results'] = [{'sceneID': i['sceneID'],
                                      'sat_type': u'L8',
                                      'path': three_digit(i['path']),
                                      'row': three_digit(i['row']),
                                      'thumbnail': i['browseURL'],
                                      'date': i['acquisitionDate'],
                                      'cloud': i['cloudCoverFull']}
                                     for i in r_dict['results']]

        return result

    def query_builder(self, paths_rows=None, lat=None, lon=None, address=None, start_date=None, end_date=None,
                      cloud_min=None, cloud_max=None):
        """ Builds the proper search syntax (query) for Landsat API.
        :param paths_rows:
            A string in this format: "003,003,004,004". Must be in pairs and separated by comma.
        :type paths_rows:
            String
        :param lat:
            The latitude
        :type lat:
            String, float, integer
        :param lon:
            The The longitude
        :type lon:
            String, float, integer
        :param address:
            The address
        :type address:
            String
        :param start_date:
            Date string. format: YYYY-MM-DD
        :type start_date:
            String
        :param end_date:
            date string. format: YYYY-MM-DD
        :type end_date:
            String
        :param cloud_min:
            float specifying the minimum percentage. e.g. 4.3
        :type cloud_min:
            float
        :param cloud_max:
            float specifying the maximum percentage. e.g. 78.9
        :type cloud_max:
            float
        :returns:
            String
        """

        query = []
        or_string = ''
        and_string = ''
        search_string = ''

        if paths_rows:
            # Coverting rows and paths to paired list
            new_array = create_paired_list(paths_rows)
            paths_rows = ['(%s)' % self.row_path_builder(i[0], i[1]) for i in new_array]
            or_string = '+OR+'.join(map(str, paths_rows))

        if start_date and end_date:
            query.append(self.date_range_builder(start_date, end_date))
        elif start_date:
            query.append(self.date_range_builder(start_date, '2100-01-01'))
        elif end_date:
            query.append(self.date_range_builder('2009-01-01', end_date))

        if cloud_min and cloud_max:
            query.append(self.cloud_cover_prct_range_builder(cloud_min, cloud_max))
        elif cloud_min:
            query.append(self.cloud_cover_prct_range_builder(cloud_min, '100'))
        elif cloud_max:
            query.append(self.cloud_cover_prct_range_builder('-1', cloud_max))

        if address:
            query.append(self.address_builder(address))
        elif (lat is not None) and (lon is not None):
            query.append(self.lat_lon_builder(lat, lon))

        if query:
            and_string = '+AND+'.join(map(str, query))

        if and_string and or_string:
            search_string = and_string + '+AND+(' + or_string + ')'
        else:
            search_string = or_string + and_string

        return search_string

    @staticmethod
    def row_path_builder(path='', row=''):
        """
        Builds row and path query.
        :param path:
            Landsat path. Must be three digits
        :type path:
            String
        :param row:
            Landsat row. Must be three digits
        :type row:
            String
        :returns:
            String
        """
        return 'path:%s+AND+row:%s' % (path, row)

    @staticmethod
    def date_range_builder(start='2013-02-11', end=None):
        """
        Builds date range query.
        :param start:
            Date string. format: YYYY-MM-DD
        :type start:
            String
        :param end:
            date string. format: YYYY-MM-DD
        :type end:
            String
        :returns:
            String
        """
        if not end:
            end = time.strftime('%Y-%m-%d')

        return 'acquisitionDate:[%s+TO+%s]' % (start, end)

    @staticmethod
    def cloud_cover_prct_range_builder(min=0, max=100):
        """
        Builds cloud cover percentage range query.
        :param min:
            float specifying the minimum percentage. Default is 0
        :type min:
            float
        :param max:
            float specifying the maximum percentage. Default is 100
        :type max:
            float
        :returns:
            String
        """
        return 'cloudCoverFull:[%s+TO+%s]' % (min, max)

    def address_builder(self, address):
        """ Builds lat and lon query from a geocoded address.
        :param address:
            The address
        :type address:
            String
        :returns:
            String
        """
        geocoded = geocode(address)
        return self.lat_lon_builder(**geocoded)

    @staticmethod
    def lat_lon_builder(lat=0, lon=0):
        """ Builds lat and lon query.
        :param lat:
            The latitude. Default is 0
        :type lat:
            float
        :param lon:
            The The longitude. Default is 0
        :type lon:
            float
        :returns:
            String
        """
        return ('upperLeftCornerLatitude:[%s+TO+1000]+AND+lowerRightCornerLatitude:[-1000+TO+%s]'
                '+AND+lowerLeftCornerLongitude:[-1000+TO+%s]+AND+upperRightCornerLongitude:[%s+TO+1000]'
                % (lat, lat, lon, lon))

if __name__ == "__main__":
    s = Search()
    tiles = s.search(paths_rows="015,033", start_date="2016-01-01", end_date="2016-01-31", limit=1000)
    for tile in tiles['results']:
        print(tile)
