ASL Dataset Summary

Overview

The ASL dataset is a Roboflow YOLOv8 export for detecting 10 static hand sign classes: A through J. The export notes state that the dataset was exported on June 6, 2026 and contains 306 images. No preprocessing or augmentation was applied in the export.

Dataset Size

Split  Images  Label Files
Train  256  256
Test / validation  50  50
Total  306  306

There are 309 total bounding box annotations across the 306 images. Most images contain one hand sign object; a small number contain more than one annotated object.

Classes

Class ID: Class
0: A
1: B
2: C
3: D
4: E
5: F
6: G
7: H
8: I
9: J

Annotation Distribution

Class: Annotations
A: 32
B: 30
C: 30
D: 31
E: 30
F: 30
G: 33
H: 30
I: 33
J: 30

The class distribution is balanced enough for an assessment demo. Classes G and I have the highest counts with 33 annotations each; most other classes have 30 or 31.

Annotation Format

Labels use YOLOv8 text format:

```text
class_id x_center y_center width height
```

The coordinate values are normalized between 0 and 1 relative to image width and height.

Example annotation:

```text
0 0.5551328125 0.4715138888888889 0.409375 0.7914305555555556
```

This sample represents class A with a bounding box centered in the image.

Data Collection Process

The source images appear to be webcam captures of hand signs, based on the file naming pattern and project scope. The dataset was then annotated with bounding boxes and exported through Roboflow in YOLOv8 format.

The pushed repository includes dataset metadata and review samples rather than the full raw image export:

File: Purpose
dataset/data.yaml: YOLO dataset configuration.
dataset/README.dataset.txt: Roboflow project metadata.
dataset/README.roboflow.txt: Roboflow export summary.
reports/annotation_samples.md: Sample YOLO annotation rows from the source export.
reports/model_evaluation.md: Model and metric summary.

Dataset Challenges

The dataset is suitable for a compact webcam demo, but it has several limits:

The dataset is small, with 306 images.
Only 10 ASL letters are included.
Lighting, distance, background, and hand position may not cover all real world webcam conditions.
The source export contains no separate valid folder, so data.yaml uses the available test split as validation for local review.
Similar looking signs can be confused when the hand is partially visible or the camera angle changes.
