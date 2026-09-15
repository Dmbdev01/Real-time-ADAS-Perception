from ultralytics import YOLO
import cv2
import numpy as np
import time


# ---------------- MODEL ----------------

model = YOLO("yolov8n.pt")


# ---------------- CAMERA ----------------

cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

FRAME_WIDTH = int(cap.get(3))
FRAME_HEIGHT = int(cap.get(4))


# ---------------- STATE ----------------

speed = 40
steering = 0

prev_areas = {}
prev_times = {}
ttc_history = []

person_memory = 0
MEMORY_TIME = 1.0


# ---------------- PD STEERING ----------------

kp = 0.005
kd = 0.002
prev_error = 0


# ---------------- MAIN LOOP ----------------

while True:

    ret, frame = cap.read()

    if not ret:
        break

    camera = frame.copy()
    stats = np.zeros((520, 520, 3), dtype=np.uint8)

    # Reset control state every frame
    brake = False
    throttle = 50

    # ---------------- LANE ZONES ----------------

    lane_width = FRAME_WIDTH // 3
    lane_center = FRAME_WIDTH // 2

    cv2.line(
        camera,
        (lane_width, 0),
        (lane_width, FRAME_HEIGHT),
        (200, 200, 200),
        2
    )

    cv2.line(
        camera,
        (2 * lane_width, 0),
        (2 * lane_width, FRAME_HEIGHT),
        (200, 200, 200),
        2
    )

    lanes = {
        "LEFT": (0, lane_width),
        "CENTER": (lane_width, 2 * lane_width),
        "RIGHT": (2 * lane_width, FRAME_WIDTH)
    }

    lane_objects = {
        "LEFT": "CLEAR",
        "CENTER": "CLEAR",
        "RIGHT": "CLEAR"
    }

    lane_distance = {
        "LEFT": 999,
        "CENTER": 999,
        "RIGHT": 999
    }

    ttc_display = 999


    # ---------------- OBJECT DETECTION ----------------

    results = model(
        frame,
        conf=0.5,
        imgsz=256,
        verbose=False
    )


    for r in results:

        for box in r.boxes:

            cls = int(box.cls[0])

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            cx = (x1 + x2) // 2

            area = (x2 - x1) * (y2 - y1)


            # ---------------- LANE ASSIGNMENT ----------------

            lane_name = None

            for name, (start, end) in lanes.items():

                if start <= cx < end:
                    lane_name = name
                    break

            if lane_name is None:
                continue


            # ---------------- DISTANCE APPROXIMATION ----------------

            distance = max(1, 50000 / area)


            # ---------------- OBJECT CLASSIFICATION ----------------

            if cls == 0:

                lane_objects[lane_name] = "PERSON"
                person_memory = time.time()

            elif cls in [2, 3, 5, 7]:

                lane_objects[lane_name] = "VEHICLE"


            lane_distance[lane_name] = min(
                lane_distance[lane_name],
                distance
            )


            # ---------------- TTC ESTIMATION ----------------

            obj_id = int(cx / 10)
            now = time.time()

            if obj_id in prev_areas and obj_id in prev_times:

                dA = area - prev_areas[obj_id]
                dt = now - prev_times[obj_id]

                if dA > 0 and dt > 0:
                    ttc = area / (dA / dt)
                else:
                    ttc = 999

            else:

                ttc = 999


            prev_areas[obj_id] = area
            prev_times[obj_id] = now

            ttc_display = min(
                ttc_display,
                ttc
            )


            # ---------------- DRAW DETECTION ----------------

            cv2.rectangle(
                camera,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )


    # ---------------- TTC SMOOTHING ----------------

    ttc_history.append(ttc_display)

    if len(ttc_history) > 5:
        ttc_history.pop(0)

    ttc_display = sum(ttc_history) / len(ttc_history)


    # ---------------- PEDESTRIAN MEMORY ----------------

    person_detected = (
        time.time() - person_memory
    ) < MEMORY_TIME


    # ---------------- RISK LEVEL ----------------

    if ttc_display < 3:

        risk = "CRITICAL"
        color = (0, 0, 255)

    elif ttc_display < 6:

        risk = "WARNING"
        color = (0, 165, 255)

    else:

        risk = "SAFE"
        color = (0, 255, 0)


    # ---------------- DECISION LOGIC ----------------

    action = "DRIVING"


    if person_detected:

        action = "BRAKE"
        brake = True
        throttle = 0

    elif ttc_display < 3:

        action = "BRAKE"
        brake = True
        throttle = 0

    elif lane_objects["CENTER"] != "CLEAR":

        if lane_objects["LEFT"] == "CLEAR":

            action = "STEER LEFT"
            lane_center = FRAME_WIDTH // 4

        elif lane_objects["RIGHT"] == "CLEAR":

            action = "STEER RIGHT"
            lane_center = 3 * FRAME_WIDTH // 4


    # ---------------- PD STEERING ----------------

    car_pos = FRAME_WIDTH // 2

    error = lane_center - car_pos

    derivative = error - prev_error

    steering = kp * error + kd * derivative

    steering = max(
        -30,
        min(30, steering * 100)
    )

    prev_error = error


    # ---------------- SPEED CONTROL ----------------

    target_speed = 60

    if brake:

        target_speed = 0

    elif throttle < 30:

        target_speed = 30

    elif throttle > 50:

        target_speed = 60


    # Smooth speed change

    speed += (
        target_speed - speed
    ) * 0.1

    speed = max(
        0,
        min(80, speed)
    )


    # ---------------- WARNINGS ----------------

    if risk == "CRITICAL":

        cv2.putText(
            camera,
            "COLLISION WARNING",
            (400, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            3
        )


    if person_detected:

        cv2.putText(
            camera,
            "PEDESTRIAN DETECTED",
            (350, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )


    # ---------------- STATS UI ----------------

    def put(text, y, c=(255, 255, 255)):

        cv2.putText(
            stats,
            text,
            (20, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            c,
            2
        )


    put(
        "ADAS SYSTEM",
        30,
        (0, 255, 255)
    )

    put(
        f"Speed: {int(speed)} km/h",
        80
    )

    put(
        f"TTC: {ttc_display:.1f} sec",
        110
    )

    put(
        f"Risk: {risk}",
        140,
        color
    )


    put(
        "LANES:",
        190,
        (0, 255, 255)
    )

    put(
        f"L: {lane_objects['LEFT']}",
        220
    )

    put(
        f"C: {lane_objects['CENTER']}",
        250
    )

    put(
        f"R: {lane_objects['RIGHT']}",
        280
    )


    put(
        "CONTROL:",
        330,
        (0, 255, 255)
    )

    put(
        f"Steering: {int(steering)} deg",
        360
    )

    put(
        f"Brake: {'ON' if brake else 'OFF'}",
        390
    )

    put(
        f"Throttle: {throttle}%",
        420
    )

    put(
        f"Action: {action}",
        470,
        color
    )


    # ---------------- DISPLAY ----------------

    cv2.imshow(
        "Camera View",
        camera
    )

    cv2.imshow(
        "Car Stats",
        stats
    )


    # ESC to exit

    if cv2.waitKey(1) & 0xFF == 27:
        break


# ---------------- CLEANUP ----------------

cap.release()
cv2.destroyAllWindows()
