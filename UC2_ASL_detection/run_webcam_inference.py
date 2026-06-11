import argparse
import os
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True

LOCAL_YOLO_CONFIG = Path(tempfile.gettempdir()) / "asl_ultralytics"
LOCAL_YOLO_CONFIG.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("YOLO_CONFIG_DIR", str(LOCAL_YOLO_CONFIG))

import cv2
from ultralytics import YOLO


def parse_args():
    base_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Run live webcam inference with a YOLO best.pt model."
    )
    parser.add_argument(
        "--model",
        default=str(base_dir / "best.pt"),
        help="Path to the trained .pt model. Defaults to ./best.pt",
    )
    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Webcam index. Try 1 or 2 if camera 0 does not open.",
    )
    parser.add_argument(
        "--conf",
        type=float,
        default=0.25,
        help="Confidence threshold for detections.",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Inference image size.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Inference device, for example 'cpu', '0', or 'cuda:0'.",
    )
    parser.add_argument("--width", type=int, default=1280, help="Camera frame width.")
    parser.add_argument("--height", type=int, default=720, help="Camera frame height.")
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Disable horizontal mirroring of the webcam feed.",
    )
    return parser.parse_args()


def open_camera(camera_index, width, height):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        cap.release()
        cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        raise RuntimeError(
            f"Could not open webcam index {camera_index}. "
            "Try --camera 1, close other camera apps, or check camera permission."
        )

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    return cap


def detection_summary(result):
    boxes = getattr(result, "boxes", None)
    if boxes is None or len(boxes) == 0:
        return "No sign detected"

    best_idx = int(boxes.conf.argmax())
    class_id = int(boxes.cls[best_idx])
    confidence = float(boxes.conf[best_idx])
    label = result.names.get(class_id, str(class_id))
    return f"{label} {confidence:.2f}"


def draw_status(frame, fps, summary):
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 82), (20, 20, 20), -1)
    cv2.putText(
        frame,
        f"ASL inference | FPS: {fps:.1f}",
        (18, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        f"Top result: {summary} | q/esc: quit | s: save",
        (18, 65),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (80, 220, 120),
        2,
        cv2.LINE_AA,
    )
    return frame


def main():
    args = parse_args()
    model_path = Path(args.model).expanduser().resolve()

    if not model_path.exists():
        print(f"Model not found: {model_path}", file=sys.stderr)
        return 1

    model = YOLO(str(model_path))
    cap = open_camera(args.camera, args.width, args.height)

    window_name = "ASL Webcam Inference"
    fps = 0.0
    previous_time = time.perf_counter()

    print("Webcam inference started. Press q or Esc to quit, s to save a frame.")

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Could not read a frame from the webcam.", file=sys.stderr)
                break

            if not args.no_mirror:
                frame = cv2.flip(frame, 1)

            results = model.predict(
                source=frame,
                imgsz=args.imgsz,
                conf=args.conf,
                device=args.device,
                verbose=False,
            )
            result = results[0]
            annotated = result.plot()

            current_time = time.perf_counter()
            elapsed = current_time - previous_time
            previous_time = current_time
            if elapsed > 0:
                fps = (0.9 * fps) + (0.1 * (1.0 / elapsed)) if fps else (1.0 / elapsed)

            annotated = draw_status(annotated, fps, detection_summary(result))
            cv2.imshow(window_name, annotated)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("s"):
                output_path = Path.cwd() / f"asl_capture_{int(time.time())}.jpg"
                cv2.imwrite(str(output_path), annotated)
                print(f"Saved {output_path}")
    finally:
        cap.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
