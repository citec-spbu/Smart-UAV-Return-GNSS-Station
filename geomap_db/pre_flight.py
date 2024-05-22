import os
import subprocess
import glob
import cv2
import tqdm

from py_src.geomap import build_geomap
from py_src.image_processing import get_embeddings


# print("Input coordinates in form of (min_lon, min_lat, max_lon, max_lat, geomap_file_name)")
# user_input = input().split(", ")
# geomap_file_name = user_input.pop()
# min_lon, min_lat, max_lon, max_lat = map(float, user_input)
#
# build_geomap(min_lon, min_lat, max_lon, max_lat, geomap_file_name)

print("The region was successfully scanned!")

masks_path = os.path.join('images', 'building')
masks = glob.glob(masks_path + '/*.png')

for mask in tqdm.tqdm(masks):
    lon, lat = mask.split(';')
    lon = lon[len(masks_path)+1:]
    lat = lat[:-4]
    embedding = get_embeddings([cv2.imread(mask)])[0]
    command = f"./add_embeddings {len(embedding)} {lon} {lat} "
    for emb_cord in embedding:
        command += f"{float(emb_cord)} "
    subprocess.run(command, shell = True, executable="/bin/bash")

print("Database filled successfully! Ready to be put on the UAV")
