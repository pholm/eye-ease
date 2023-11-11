import cv2
import numpy as np
import dlib
from imutils import face_utils
from server import TimeSeriesDataProcessor

processor = TimeSeriesDataProcessor(
    window_size=50, alarm_threshold=500, stress_refil_threshold=10000
)


def extract_eye(image, eye_points):
    eye = cv2.convexHull(eye_points)
    x, y, w, h = cv2.boundingRect(eye)
    eye = image[y : y + h, x : x + w]
    return (
        eye,
        (x, y, w, h),
        eye_points,
    )  # Return the eye points in their original format


def find_pupil(eye):
    gray_eye = cv2.cvtColor(eye, cv2.COLOR_BGR2GRAY)
    _, threshold_eye = cv2.threshold(gray_eye, 70, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(
        threshold_eye, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE
    )
    contours = sorted(contours, key=lambda x: cv2.contourArea(x), reverse=True)
    for cnt in contours:
        (x, y, w, h) = cv2.boundingRect(cnt)
        return (x + w // 2, y + h // 2)
    return None


# Initialize dlib's face detector and landmark predictor
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Start webcam
cap = cv2.VideoCapture(0)
i = 0
while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)

    for face in faces:
        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)

        # Extract eyes and their points
        left_eye, left_eye_rect, left_eye_points = extract_eye(frame, landmarks[36:42])
        right_eye, right_eye_rect, right_eye_points = extract_eye(
            frame, landmarks[42:48]
        )

        # Find the pupil in each eye
        left_pupil = find_pupil(left_eye)
        right_pupil = find_pupil(right_eye)
        # Draw contours around the eyes
        cv2.drawContours(frame, [left_eye_points], -1, (0, 255, 0), 1)
        cv2.drawContours(frame, [right_eye_points], -1, (0, 255, 0), 1)

        if left_pupil:
            cv2.circle(
                frame,
                (left_pupil[0] + left_eye_rect[0], left_pupil[1] + left_eye_rect[1]),
                2,
                (0, 0, 255),
                2,
            )
        if right_pupil:
            cv2.circle(
                frame,
                (
                    right_pupil[0] + right_eye_rect[0],
                    right_pupil[1] + right_eye_rect[1],
                ),
                2,
                (0, 0, 255),
                2,
            )

    cv2.imshow("Pupil Tracker", frame)
    if left_pupil and right_pupil:
        center_of_left_eye_rect = (
            left_eye_rect[0] + left_eye_rect[2] // 2,
            left_eye_rect[1] + left_eye_rect[3] // 2,
        )
        center_of_right_eye_rect = (
            right_eye_rect[0] + right_eye_rect[2] // 2,
            right_eye_rect[1] + right_eye_rect[3] // 2,
        )
        left_pupil_offset = (
            left_pupil[0] - center_of_left_eye_rect[0],
            left_pupil[1] - center_of_left_eye_rect[1],
        )
        right_pupil_offset = (
            right_pupil[0] - center_of_right_eye_rect[0],
            right_pupil[1] - center_of_right_eye_rect[1],
        )
        processor._process_eye_data(
            [
                {
                    "t": "L",
                    "m": [
                        [
                            -left_pupil_offset[0],
                            -(left_pupil_offset[0] + left_pupil_offset[1]),
                            -left_pupil_offset[1],
                            left_pupil_offset[0],
                            (left_pupil_offset[0] + left_pupil_offset[1]),
                            left_pupil_offset[1],
                        ]
                    ],
                    "i": [i],
                },
                {
                    "t": "R",
                    "m": [
                        [
                            right_pupil_offset[0],
                            (right_pupil_offset[0] + right_pupil_offset[1]),
                            right_pupil_offset[1],
                            -right_pupil_offset[0],
                            -(right_pupil_offset[0] + right_pupil_offset[1]),
                            -right_pupil_offset[1],
                        ]
                    ],
                    "i": [i],
                },
            ]
        )
    print(processor.get_running_average("L"))
    i += 1
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
