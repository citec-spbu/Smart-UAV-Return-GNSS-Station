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

![Исаакиевский собор](./predicted_isakiy.png)
![ПУНК](./predicted_punk.png)
![ПМ-ПУ](./predicted_pm.png)
