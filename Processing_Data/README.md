.\pothole-env-export\Scripts\Activate


## Testing the live Camera

```bash
python detect.py --weights .\best_windows_exp5.pt --data pothole_data.yaml --source 1 --vid-stride 3 --view-img
```

## Testing live video sim
```bash
python detect.py --weights best_windows_exp5.pt --data pothole_data.yaml --source dashboard_short.mp4 --imgsz 640 --view-img
```

### Testing live video sim every 1/3 frame
```bash
python detect.py --weights best-int8-320.tflite --data pothole_data.yaml --source dashboard_short.mp4 --imgsz 320 --vid-stride 3 --view-img
```