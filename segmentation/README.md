# Instance segmentation

**Model:** YOLOv8n-seg

## Usage

```bash
pip install ultralytics
```

```python
from ultralytics import YOLO
model = YOLO('dronuniver_yolov8nseg.pt')
```

```python
from PIL import Image
img = Image.open(img_name)
res = model(img)[0]
```

## Results

![Исаакиевский собор](segmentation/predicted_isakiy.jpg)
![ПУНК](segmentation/predicted_punk.jpg)
![ПМ-ПУ](segmentation/predicted_pm.jpg)
