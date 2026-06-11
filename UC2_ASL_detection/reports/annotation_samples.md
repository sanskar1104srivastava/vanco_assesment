ASL Annotation Samples

The ASL dataset uses YOLOv8 bounding box annotation format.

```text
class_id x_center y_center width height
```

All box coordinates are normalized between 0 and 1 relative to image width and height.

Class Map

Class ID: Letter
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

Samples

Split  Image  Label
Train  WIN_20260605_18_13_41_Pro_jpg.rf.lTMzkEyd2MNBmkqkcxUK.jpg  0 0.5551328125 0.4715138888888889 0.409375 0.7914305555555556
Train  WIN_20260605_18_13_45_Pro_jpg.rf.GMRkE6u6LwSAilofgPky.jpg  0 0.5246640625000001 0.4148055555555556 0.2971015625 0.6224722222222222
Test  WIN_20260606_14_01_03_Pro_jpg.rf.vPBdRp7Y0XDZ5qmMzSRe.jpg  0 0.48460156249999997 0.5881944444444445 0.2236640625 0.4375
Test  WIN_20260606_14_01_19_Pro_jpg.rf.xDQ1kIkExKA2etOOKeGo.jpg  1 0.48950781250000003 0.6095833333333333 0.215625 0.7024861111111111
Test  WIN_20260606_14_01_44_Pro_jpg.rf.fHcs2SuBaswteNWLcpHG.jpg  2 0.2753359375 0.7859166666666667 0.3653984375 0.42818055555555556

These examples show one object per image, where the first value is the class ID and the remaining four values define the bounding box.
