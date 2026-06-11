ASL Model Evaluation

Evaluation Artifacts

The evaluation evidence for the ASL detector is stored in this folder:

Artifact: Description
training_results.csv: Per epoch training metrics from the YOLO run.
training_results.png: Loss, precision, recall, and mAP curves.
confusion_matrix.png: Raw confusion matrix.
confusion_matrix_normalized.png: Normalized confusion matrix.
f1_curve.png: F1 score by confidence threshold.
precision_curve.png: Precision by confidence threshold.
recall_curve.png: Recall by confidence threshold.
precision_recall_curve.png: Precision recall tradeoff.

Key Metrics

The best observed mAP50 to 95 row in training_results.csv is epoch 54:

Metric: Value
Precision: 0.92037
Recall: 0.91934
mAP50: 0.96833
mAP50 to 95: 0.65328

The final training row is epoch 79:

Metric: Value
Precision: 0.92866
Recall: 0.80974
mAP50: 0.96833
mAP50 to 95: 0.60458

The final row preserves high precision and mAP50, but recall and mAP50 to 95 are lower than the best epoch. For reviewer discussion, epoch 54 is the strongest recorded checkpoint by stricter localization quality.

Confusion Matrix Discussion

The confusion matrix shows strong detection for several classes:

Class C is correctly detected for all 5 test examples.
Classes F and G are also correctly detected for all 5 examples shown in the matrix.
Classes A, B, and D each show 4 correct detections out of 5 examples.

The weaker areas are visible in the normalized confusion matrix:

Class H and class J show lower recall in the available test examples.
Some missed detections are assigned to background.
Class E has confusion with nearby hand shapes, including A and B.

Because the test split is small, the confusion matrix should be read as demo evidence rather than a production benchmark.

Failure Cases

Likely failure cases include:

Hand signs partly outside the camera frame.
Very bright or dark lighting.
Backgrounds with skin colored objects.
Camera angles that differ from the captured training examples.
Fast movement or motion blur during live webcam inference.
Similar hand shapes between adjacent ASL letters in the limited A to J class set.

Robustness Observations

The detector is good enough for a controlled local demo with clear hand placement and normal lighting. It is not yet robust enough for broad deployment. A production version should expand the dataset across users, skin tones, backgrounds, camera devices, and lighting conditions. It should also add a true validation split and evaluate on a separate holdout set collected from people not seen during training.

Conclusion

The ASL detector has a complete demo path: dataset, trained checkpoint, evaluation artifacts, confusion matrix, and webcam inference script. The results support an assessment demonstration, while the limitations are clear and documented.
