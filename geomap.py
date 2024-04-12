import time
import cv2
import numpy as np
import osmapi

from geopy.distance import geodesic

COLORSCHEME = {
        'building' : (0, 0, 255),
        'water' : (255, 0, 0),
        'natural' : (0, 255, 0),
        'grass' : (0, 128, 0),
        'leisure' : (0, 128, 128),
        'highway' : (0, 128, 128)
}

VISUALIZE_OBJECTS = [
    'bridge',
    'building',
    'water',
    'grass',
    'natural',
    'leisure',
    'highway'
]

LIMIT_WIDTH = LIMIT_HEIGHT = 1000   # Does not allow api.Map() to overfit the request

LIMIT_NODE_AMOUNT = 700             # Does not allow api.WaysGet() and api.NodesGet() to overfit the request

api = osmapi.OsmApi()

def handle_osm_api_error(func):
    """
    A decorator to overcome OSM's bandwidth limit exceeded error
    """
    def wrapper(*args, **kwargs):
        try:
            return_value = func(*args, **kwargs)
        except osmapi.ApiError as error:
            print(error.reason)
            time_to_sleep = int(error.payload.split()[-2]) + 1
            time.sleep(time_to_sleep)
            return_value = func(*args, **kwargs)
            print(f"APIError got handled, slept for {time_to_sleep} seconds")
        except AssertionError:
            return_value = []
        return return_value
    return wrapper

@handle_osm_api_error
def download_sector(sector : list[float]) -> list[dict]:
    assert len(sector) == 4
    sectors_nodes = api.Map(*sector)
    return sectors_nodes

@handle_osm_api_error
def download_ways(relation_id : int) -> dict:
    relation = api.RelationGet(relation_id)
    ways_ids = []
    relation_members = relation['member']
    for member in relation_members:
        if member['type'] == 'way':
            ways_ids.append(member['ref'])
    if len(ways_ids) > LIMIT_NODE_AMOUNT:
        return {}
    ways = api.WaysGet(ways_ids)
    return ways

@handle_osm_api_error
def download_nodes(nodes_ids : list[int]) -> dict:
    if len(nodes_ids) > LIMIT_NODE_AMOUNT:
        return {}
    nodes = api.NodesGet(nodes_ids)
    return nodes

#TODO Develope a function to choose the best tag describing an object

class Geomap:
    def __init__(self, min_lon : float, min_lat : float, max_lon : float, max_lat : float) -> None:
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.max_lat = max_lat
        self.__width = int(geodesic(
            (self.min_lat, self.min_lon), (self.min_lat, self.max_lon)
            ).kilometers * 1000)
        self.__height = int(geodesic(
            (self.min_lat, self.min_lon), (self.max_lat, self.min_lon)
            ).kilometers * 1000)
        self.image = None
        self.__nodes = None
        self.__ways = None
        self.__relations = None

    def __area_sectorization(self) -> list[list[float]]:
        """
        Breaks down the map into sectors of given size, in order to
        make each sector to be callable via API
        """
        width_ratio = int(np.ceil(self.__width / LIMIT_WIDTH))
        height_ratio = int(np.ceil(self.__height / LIMIT_HEIGHT))
        delta_lon = (self.max_lon - self.min_lon) / width_ratio
        delta_lat = (self.max_lat - self.min_lat) / height_ratio
        sectors = []
        for i in range(width_ratio):
            for j in range(height_ratio):
                sectors.append([self.min_lon + i*delta_lon, self.min_lat + j*delta_lat,
                                self.min_lon + (i+1)*delta_lon, self.min_lat + (j+1)*delta_lat])
        return sectors

    def download_map(self) -> list[dict]:
        """
        Downloading given map from OpenStreetMaps.
        Might take a while to be finished
        """
        sectors = self.__area_sectorization()
        all_nodes = []
        for i, sector in enumerate(sectors, start=1):
            all_nodes += download_sector(sector)
            if i % 10 == 0:
                print(f'{i}/{len(sectors)} sectors were downloaded')

        self.__nodes = {
            node['data']['id'] : node['data'] for node in all_nodes
            if node['type'] == 'node'
        }
        self.__ways = {
            node['data']['id'] : node['data'] for node in all_nodes
            if node['type'] == 'way' and 'tag' in node['data'].keys() and any(tag in VISUALIZE_OBJECTS for tag in node['data']['tag'].keys())
        }
        self.__relations = {
            node['data']['id'] : node['data'] for node in all_nodes
            if node['type'] == 'relation' and 'tag' in node['data'].keys() and node['data']['tag']['type'] == 'multipolygon' and any(tag in VISUALIZE_OBJECTS for tag in node['data']['tag'].keys())
        }
        return all_nodes

    def __relations_visualization(self, image):
        """
        Drawing OSM relations
        """
        for i, relation_id in enumerate(self.__relations.keys(), start=1):
            relation = self.__relations[relation_id]
            relation_tags = relation['tag']
            for tag in relation_tags:
                if tag in COLORSCHEME.keys():
                    main_tag = tag
                    break
            else:
                continue
            ways_in_relation = download_ways(relation_id)

            for way_id in ways_in_relation.keys():
                way_data = ways_in_relation[way_id]
                node_cords = []
                way_nodes = download_nodes(way_data['nd'])
                for node_id in way_data['nd']:
                    node = way_nodes[node_id]
                    if not (self.min_lat < node['lat'] < self.max_lat and
                            self.min_lon < node['lon'] < self.max_lon):
                        continue
                    node_cord_y = int(geodesic((self.max_lat, self.min_lon), (node['lat'], self.min_lon)).kilometers * 1000)
                    node_cord_x = int(geodesic((self.max_lat, self.min_lon), (self.max_lat, node['lon'])).kilometers * 1000)
                    node_cords.append([node_cord_x, node_cord_y])
                node_cords = np.array(node_cords, np.int32)
                node_cords = node_cords.reshape((-1, 1, 2))
                cv2.polylines(image, [node_cords], True, COLORSCHEME[main_tag])
            if i % 100 == 0:
                print(f"{i}/{len(self.__relations)} relations were preprocessed")
        return image

    def __ways_visualization(self, image):
        """
        Drawing OSM ways
        """
        for i, way_id in enumerate(self.__ways.keys(), start=1):
            way = self.__ways[way_id]
            way_tags = way['tag']
            for tag in way_tags:
                if tag in COLORSCHEME.keys():
                    main_tag = tag
                    break
            else:
                continue
            node_cords = []
            for node_id in way['nd']:
                node = self.__nodes[node_id]
                if not (self.min_lat < node['lat'] < self.max_lat and
                            self.min_lon < node['lon'] < self.max_lon):
                        continue
                node_cord_y = int(geodesic((self.max_lat, self.min_lon), (node['lat'], self.min_lon)).kilometers * 1000)
                node_cord_x = int(geodesic((self.max_lat, self.min_lon), (self.max_lat, node['lon'])).kilometers * 1000)
                node_cords.append([node_cord_x, node_cord_y])
            node_cords = np.array(node_cords, np.int32)
            node_cords = node_cords.reshape((-1, 1, 2))
            cv2.polylines(image, [node_cords], True, COLORSCHEME[main_tag])
            if i % 100 == 0:
                print(f"{i}/{len(self.__ways)} ways were preprocessed")
        return image

    def get_map_visualization(self):
        """
        Making an image out of information, which API has given
        """
        assert self.__nodes, "Map is not downloaded yet!\nRun download_map() method first!"
        image = np.zeros((self.__width, self.__height, 3), np.uint8)

        image = self.__relations_visualization(image)
        image = self.__ways_visualization(image)

        self.image = image
        return image

    def save_image_as(self, file_name : str = 'map.png'):
        """
        Saves map as an image
        """
        cv2.imwrite(file_name, self.image)


if __name__ == '__main__':
    geomap = Geomap(30.2555, 59.9080, 30.3446, 59.9600)
    geomap.download_map()
    geomap.get_map_visualization()
    geomap.save_image_as('map.png')
