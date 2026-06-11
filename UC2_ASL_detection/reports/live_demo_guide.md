ASL Live Demo Guide

This guide is written for a reviewer who wants to run the webcam demo quickly.

Install Dependencies

Open PowerShell in the UC2_ASL_detection folder:

```powershell
cd D:\vanco_assesment\UC2_ASL_detection
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

Connect Webcam

Use the laptop webcam or connect an external webcam. Close other applications that may already be using the camera.

Run Application

Start the demo:

```powershell
python run_webcam_inference.py
```

If the first camera does not open, try:

```powershell
python run_webcam_inference.py --camera 1
```

Expected Output

A window named ASL Webcam Inference should open. The window shows:

Live camera video.
Bounding boxes around detected hand signs.
The predicted ASL class.
Confidence score.
Frames per second.

Press q or Esc to quit. Press s to save the current annotated frame.

Troubleshooting

Issue: What To Try
Webcam does not open: Try another camera index such as camera 1 or camera 2.
Black camera window: Check camera permissions and close video call apps.
Model not found: Confirm best.pt exists in the UC2_ASL_detection folder.
Slow performance: Run on a smaller camera resolution or use CPU friendly settings.
No detection: Hold one sign clearly in front of the camera with good lighting.
Wrong class: Keep the hand centered and avoid motion blur.

Optional lower resolution run:

```powershell
python run_webcam_inference.py --width 640 --height 480
```
