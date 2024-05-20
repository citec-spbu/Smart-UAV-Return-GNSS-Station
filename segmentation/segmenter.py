import cv2
import numpy as np
from typing import List
from ultralytics import YOLO


_model = YOLO('dronuniver_yolov8nseg.pt')


def segment_buildings(img_name: str) -> List[np.ndarray]:
    '''
    Params:
        img_name: str - image filename
    
    Returns:
        result: List[np.ndarray] - list of cropped masked buildings \
            (numpy array)
    '''
    clear_img = cv2.imread(img_name)
    segmented = _model(img_name)[0]
    masks = segmented.masks.data.numpy()

    result = [None] * len(masks)

    for i in range(len(masks)):
        img = clear_img.copy()
        mask0 = cv2.resize(masks[i], dsize=(img.shape[-2::-1])).astype(np.uint8)
        masked_img = cv2.bitwise_and(img, img, mask=mask0)
        non_zero_coords = np.argwhere(mask0 > 0)
        y_min, x_min = non_zero_coords.min(axis=0)
        y_max, x_max = non_zero_coords.max(axis=0)
        cropped_image = masked_img[y_min:y_max+1, x_min:x_max+1]
        result[i] = cropped_image[:, :, ::-1]

    return result


if __name__ == '__main__':
    buildings = segment_buildings('test.jpg')
    print(f'{len(buildings)} buildings segmented')

    import matplotlib.pyplot as plt

    if len(buildings):
        plt.imshow(buildings[0])
        plt.show()
