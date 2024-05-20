"""
This module provides you with all needed functionality to visualize OSM maps
"""

import time
import os
import cv2
import numpy as np
import osmapi
import osmium

from geopy.distance import geodesic
from tqdm import tqdm

COLORSCHEME = {
        'yes' : (0, 0, 255),
        'retail' : (0, 0, 255),
        'cathedral' : (0, 0, 128),
        'school' : (0, 0, 128),
        'dormitory' : (0, 0, 128),
        'hospital' : (0, 0, 128),
        'apartments' : (0, 0, 255),
        'water' : (255, 0, 0),
        'wood' : (0, 255, 0),
        "wetland": (64, 255, 0),
        'grass' : (0, 128, 0),
        'park' : (0, 64, 0),
        'sand' : (128, 128, 0),
        'pitch' : (0, 64, 128),
        'fitness_station' : (0, 64, 128),
        'playground' : (0, 64, 128),
        'cemetery' : (0, 64, 255),
        'primary' : (0, 128, 128),
        'tertiary' : (0, 128, 128),
        'secondary' : (0, 128, 128),
        'residential' : (0, 128, 128),
        'service' : (0, 128, 128),
        'construction' : (64, 64, 64),
        'wall' : (255, 0, 128)
}

VISUALIZE_OBJECTS = [
    'bridge',
    'building',
    'water',
    'landuse',
    'natural',
    'leisure',
    'highway',
    'barrier'
]

LIMIT_WIDTH = LIMIT_HEIGHT = 1000   # Does not allow api.Map() to overfit the request

LIMIT_NODE_AMOUNT = 700             # Does not allow api.WaysGet() and api.NodesGet() to overfit the request

def get_description(tags : dict) -> str:
    """
    Returns description of the object for it to be visualized properly
    """
    for key, value in tags.items():
        if key in VISUALIZE_OBJECTS and value in COLORSCHEME.keys():
            return key, value
    return None

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
    """
    Downloads map sectors from OSM
    """
    assert len(sector) == 4
    sectors_nodes = api.Map(*sector)
    return sectors_nodes

@handle_osm_api_error
def download_ways(relation_id : int) -> dict:
    """
    Downloads ways from OSM
    """
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
    """
    Downloads nodes from OSM
    """
    if len(nodes_ids) > LIMIT_NODE_AMOUNT:
        return {}
    nodes = api.NodesGet(nodes_ids)
    return nodes

class GeomapFromAPI:
    """
    Tool to interact with OSM API.
    You'd better use GeomapFromFile for better performance.
    """
    def __init__(self, min_lon : float, min_lat : float, max_lon : float, max_lat : float) -> None:
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.max_lat = max_lat
        self.__height = int(geodesic(
            (self.min_lat, self.min_lon), (self.min_lat, self.max_lon)
            ).kilometers * 1000)
        self.__width = int(geodesic(
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
            if node['type'] == 'way' and 'tag' in node['data'].keys() and \
                any(tag in VISUALIZE_OBJECTS for tag in node['data']['tag'].keys())
        }
        self.__relations = {
            node['data']['id'] : node['data'] for node in all_nodes
            if node['type'] == 'relation' and 'tag' in node['data'].keys() and \
                  node['data']['tag']['type'] == 'multipolygon' and \
                    any(tag in VISUALIZE_OBJECTS for tag in node['data']['tag'].keys())
        }
        return all_nodes


    def __relations_visualization(self, image):
        """
        Drawing OSM relations
        """
        for i, relation_id, relation in enumerate(self.__relations.items(), start=1):
            main_tag = get_description(relation['tag'])
            if not main_tag:
                continue
            ways_in_relation = download_ways(relation_id)
            for _, way_data in ways_in_relation.items():
                node_cords = []
                way_nodes = download_nodes(way_data['nd'])
                for node_id in way_data['nd']:
                    node = way_nodes[node_id]
                    if not (self.min_lat < node['lat'] < self.max_lat and
                            self.min_lon < node['lon'] < self.max_lon):
                        continue
                    node_cord_y = int(geodesic(
                        (self.max_lat, self.min_lon), (node['lat'], self.min_lon)
                        ).kilometers * 1000)
                    node_cord_x = int(geodesic(
                        (self.max_lat, self.min_lon), (self.max_lat, node['lon'])
                        ).kilometers * 1000)
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
        for i, _, way in enumerate(self.__ways.items(), start=1):
            way_tags = way['tag']
            main_tag = get_description(way_tags)
            if not main_tag:
                continue
            node_cords = []
            for node_id in way['nd']:
                node = self.__nodes[node_id]
                if not (self.min_lat < node['lat'] < self.max_lat and \
                    self.min_lon < node['lon'] < self.max_lon):
                    continue
                node_cord_y = int(geodesic(
                    (self.max_lat, self.min_lon), (node['lat'], self.min_lon)
                    ).kilometers * 1000)
                node_cord_x = int(geodesic(
                    (self.max_lat, self.min_lon), (self.max_lat, node['lon'])
                    ).kilometers * 1000)
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
        assert self.image, "Image is not created yet"
        cv2.imwrite(file_name, self.image)


class GeomapFromFile(osmium.SimpleHandler):
    """
    Tool for extracting OSM data from given file.
    Appropriate data can be found at https://download.geofabrik.de/
    """
    def __init__(self, min_lon : float, min_lat : float, max_lon : float, max_lat : float) -> None:
        osmium.SimpleHandler.__init__(self)
        self.min_lon = min_lon
        self.min_lat = min_lat
        self.max_lon = max_lon
        self.max_lat = max_lat
        self.image = None
        self.__areas = []
        self.__ways = []

    def __node_is_acceptable(self, node):
        """
        Checks if node is in the restricted area
        """
        if self.min_lat <= node.location.lat <= self.max_lat and \
           self.min_lon <= node.location.lon <= self.max_lon:
            return True
        return False

    def area(self, area):
        """
        Osmium library uses this method to process areas from .osm file
        """
        if area.visible:
            area_dict = {
                'area_id' : area.id,
                'tags' : {tag.k : tag.v for tag in area.tags},
                'outer_rings' : [],
                'inner_rings' : []
            }
            for outer_ring in area.outer_rings():
                nodes = [node for node in outer_ring if self.__node_is_acceptable(node)]
                area_dict['outer_rings'].append(nodes)
                for inner_ring in area.inner_rings(outer_ring):
                    nodes = [node for node in inner_ring if self.__node_is_acceptable(node)]
                    area_dict['inner_rings'].append(nodes)
            self.__areas.append(area_dict)

    def way(self, way):
        """
        Osmium library uses this method to process ways from .osm file
        """
        if way.visible and not way.is_closed():
            way_dict = {
                'way_id' : way.id,
                'tags' : {tag.k : tag.v for tag in way.tags},
                'nodes' : [node for node in way.nodes if self.__node_is_acceptable(node)]
            }
            self.__ways.append(way_dict)

    def __extract_object_mask(self, area_mask, area_coordinates : list[float], object_tag : list[str, str]):
        """
        Saves object's mask as a file in format "images/<object_tag>/<object_location>.png
        """
        crop_above = int(geodesic(
                        (self.max_lat, self.min_lon), (area_coordinates[2], self.min_lon)
                        ).kilometers * 1000)
        crop_under = int(geodesic(
                        (self.max_lat, self.min_lon), (area_coordinates[0], self.min_lon)
                        ).kilometers * 1000)
        crop_left = int(geodesic(
                        (self.max_lat, self.min_lon), (self.max_lat, area_coordinates[1])
                        ).kilometers * 1000)
        crop_right = int(geodesic(
                        (self.max_lat, self.min_lon), (self.max_lat, area_coordinates[3])
                        ).kilometers * 1000)

        object_location = ((area_coordinates[2] + area_coordinates[0])/2, (area_coordinates[3] + area_coordinates[1])/2)

        object_mask = area_mask[crop_above:crop_under, crop_left:crop_right]
        if not os.path.exists(f"images/{object_tag[0]}"):
            os.makedirs(f"images/{object_tag[0]}")
        if object_mask.size:
            cv2.imwrite(f"images/{object_tag[0]}/{object_location[0]};{object_location[1]}.png", object_mask)

    def __visualize_area(self, image, extract_mask : bool = True ):
        """
        Draws areas
        """
        for area in tqdm(self.__areas):
            main_tag = get_description(area['tags'])
            if not main_tag:
                continue
            area_mask = np.zeros(image.shape, np.uint8)
            max_lat, min_lat = -90, 90
            max_lon, min_lon = -180, 180
            has_outer_rings = has_inner_rings = False
            for outer_ring in area['outer_rings']:
                outer_node_cords = []
                for node in outer_ring:
                    max_lat, min_lat = max(node.location.lat, max_lat), min(node.location.lat, min_lat)
                    max_lon, min_lon = max(node.location.lon, max_lon), min(node.location.lon, min_lon)
                    node_cord_y = int(geodesic(
                        (self.max_lat, self.min_lon), (node.location.lat, self.min_lon)
                        ).kilometers * 1000)
                    node_cord_x = int(geodesic(
                        (self.max_lat, self.min_lon), (self.max_lat, node.location.lon)
                        ).kilometers * 1000)
                    outer_node_cords.append([node_cord_x, node_cord_y])
                if outer_node_cords:
                    has_outer_rings = True
                    outer_node_cords = np.array(outer_node_cords, np.int32)
                    outer_node_cords = outer_node_cords.reshape((-1, 1, 2))
                    cv2.drawContours(area_mask, [outer_node_cords], -1, COLORSCHEME[main_tag[1]], -1)

            for inner_ring in area['inner_rings']:
                inner_node_cords = []
                for node in inner_ring:
                    max_lat, min_lat = max(node.location.lat, max_lat), min(node.location.lat, min_lat)
                    max_lon, min_lon = max(node.location.lon, max_lon), min(node.location.lon, min_lon)
                    node_cord_y = int(geodesic(
                        (self.max_lat, self.min_lon), (node.location.lat, self.min_lon)
                        ).kilometers * 1000)
                    node_cord_x = int(geodesic(
                        (self.max_lat, self.min_lon), (self.max_lat, node.location.lon)
                        ).kilometers * 1000)
                    inner_node_cords.append([node_cord_x, node_cord_y])
                if inner_node_cords:
                    has_inner_rings = True
                    inner_node_cords = np.array(inner_node_cords, np.int32)
                    inner_node_cords = inner_node_cords.reshape((-1, 1, 2))
                    if has_outer_rings:
                        cv2.drawContours(area_mask, [inner_node_cords], -1, (0, 0, 0), -1)
                    else:
                        cv2.drawContours(area_mask, [inner_node_cords], -1, COLORSCHEME[main_tag[1]], -1)
            if extract_mask and (has_outer_rings or has_inner_rings):
                self.__extract_object_mask(area_mask, [min_lat, min_lon, max_lat, max_lon], main_tag)
            image = cv2.addWeighted(image, 1, area_mask, 1, 0)

        return image

    def __visualize_ways(self, image):
        """
        Draws ways
        """
        for way in self.__ways:
            main_tag = get_description(way['tags'])
            if not main_tag:
                continue
            node_cords = []
            for node in way['nodes']:
                node_cord_y = int(geodesic(
                    (self.max_lat, self.min_lon), (node.location.lat, self.min_lon)
                    ).kilometers * 1000)
                node_cord_x = int(geodesic(
                    (self.max_lat, self.min_lon), (self.max_lat, node.location.lon)
                    ).kilometers * 1000)
                node_cords.append([node_cord_x, node_cord_y])
            if node_cords:
                node_cords = np.array(node_cords, np.int32)
                node_cords = node_cords.reshape((-1, 1, 2))
                cv2.polylines(image, [node_cords], False, COLORSCHEME[main_tag[1]], 6)

        return image

    def visualize_map(self):
        """
        Visualizing the map
        """
        height = int(geodesic(
            (self.min_lat, self.min_lon), (self.min_lat, self.max_lon)
            ).kilometers * 1000)
        width = int(geodesic(
            (self.min_lat, self.min_lon), (self.max_lat, self.min_lon)
            ).kilometers * 1000)

        image = np.zeros((width, height, 3), np.uint8)

        image = self.__visualize_area(image)
        image = self.__visualize_ways(image)

        self.image = image
        return image

    def save_image_as(self, file_name : str = 'images/map.png'):
        """
        Saves map as an image
        """
        if not os.path.exists("images"):
            os.makedirs("images")
        cv2.imwrite(file_name, self.image)

def build_geomap(min_lon : float, min_lat : float, max_lon : float, max_lat : float, geomap_file = "data/northwestern-fed-district-latest.osm.pbf") -> None:
    geomap = GeomapFromFile(min_lon, min_lat, max_lon, max_lat)
    geomap.apply_file(geomap_file)
    geomap.visualize_map()
    geomap.save_image_as()


if __name__ == '__main__':
    build_geomap(30.2775, 59.9091, 30.2974, 59.9164)
