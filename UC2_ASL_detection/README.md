UC2 ASL Detection

This folder contains the American Sign Language detection use case for the AI Solution Architect assessment. The solution detects static ASL hand signs from webcam frames using a trained YOLO model.

Problem Statement

The goal is to detect hand signs for ASL letters A through J in a live camera feed. The reviewer should be able to inspect the dataset, review model evidence, and run the webcam demo locally.

Dataset

The dataset was exported from Roboflow on June 6, 2026. It contains 306 images across 10 classes: A, B, C, D, E, F, G, H, I, and J.

Split  Images  Labels
Train  256  256
Test / validation  50  50

The pushed repository keeps dataset metadata, a dataset summary, and annotation samples. The full raw image and label export is kept out of Git to keep the public submission lean.

Labels use YOLOv8 bounding box format. See reports/annotation_samples.md for sample annotation rows from the source export.

Model

The trained model checkpoint is:

```text
best.pt
```

The model is loaded by run_webcam_inference.py using Ultralytics YOLO. The script opens a webcam, runs inference frame by frame, and shows an annotated camera window.

Training Notebook

The Kaggle training notebook is stored at:

```text
training/vanco-uc2.ipynb
```

It documents the Ultralytics setup, dataset configuration, YOLO training run, and result export used for the ASL model evidence.

Evaluation Summary

The ASL training run includes real metric artifacts under reports/:

Artifact: Purpose
reports/training_results.csv: Per epoch training and validation metrics.
reports/training_results.png: Training curves for loss, precision, recall, and mAP.
reports/confusion_matrix.png: Raw confusion matrix.
reports/confusion_matrix_normalized.png: Normalized confusion matrix.
reports/f1_curve.png: F1 confidence curve.
reports/precision_curve.png: Precision confidence curve.
reports/recall_curve.png: Recall confidence curve.
reports/precision_recall_curve.png: Precision recall curve.

Best observed training run metrics occurred at epoch 54:

Metric: Value
Precision: 0.92037
Recall: 0.91934
mAP50: 0.96833
mAP50 to 95: 0.65328

See reports/model_evaluation.md for the full reviewer summary.

Run The Webcam Demo

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python run_webcam_inference.py
```

The webcam window should show bounding boxes and the top detected ASL class. Press q or Esc to quit. Press s to save a frame.

If camera index 0 does not open, try:

```powershell
python run_webcam_inference.py --camera 1
```

Folder Guide

Path: Contents
dataset/: Roboflow metadata and dataset configuration.
training/: Kaggle notebook used to train and export the YOLO ASL model.
best.pt: Trained YOLO checkpoint used for the live demo.
run_webcam_inference.py: OpenCV webcam inference script.
reports/: Dataset summary, annotation samples, evaluation, demo, and metric artifacts.
diagrams/: ASL detection architecture diagram.
screenshots/: Place for demo screenshots captured during final review.

Reproducibility Notes

The current repository is optimized for review and live inference. The dataset YAML uses the available test split as validation because the source Roboflow export contains train and test folders, but no valid folder.
