import os
import subprocess
import glob
import cv2
import tqdm
import torch

from PIL import Image
from transformers import AutoImageProcessor, ResNetModel
from torchvision.transforms.functional import pil_to_tensor

from py_src.geomap import build_geomap

print("Input coordinates in form of (min_lon, min_lat, max_lon, max_lat, geomap_file_name)")
user_input = input().split(", ")
geomap_file_name = user_input.pop()
min_lon, min_lat, max_lon, max_lat = map(float, user_input)

build_geomap(min_lon, min_lat, max_lon, max_lat, geomap_file_name)

print("The region was successfully scanned!")

emb_processor = AutoImageProcessor.from_pretrained("microsoft/resnet-50")
emb_model = ResNetModel.from_pretrained("nn_models")

masks_path = os.path.join('images', 'building')
masks = glob.glob(masks_path + '/*.png')

for mask in tqdm.tqdm(masks):
    lon, lat = mask.split(';')
    lon = lon[len(masks_path)+1:]
    lat = lat[:-4]
    mask_img = cv2.imread(mask)
    mask_img = cv2.cvtColor(mask_img, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(mask_img)
    im_pil = torch.clamp(pil_to_tensor(im_pil.resize((32, 32))) / 255, 0, 1)
    inputs = emb_processor(im_pil, return_tensors="pt")
    with torch.no_grad():
        embedding = emb_model(**inputs).pooler_output[0, :, 0, 0].tolist()
    command = f"./build/add_embeddings {len(embedding)} {lon} {lat} "
    for emb_cord in embedding:
        command += f"{float(emb_cord)} "
    subprocess.run(command, shell = True, executable="/bin/bash")


print("Database filled successfully! Ready to be put on the UAV")
