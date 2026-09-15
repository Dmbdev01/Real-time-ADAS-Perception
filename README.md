# Real-Time ADAS Perception & Decision Prototype

A real-time Advanced Driver Assistance System (ADAS) prototype developed as part of a larger drive-by-wire vehicle project.

The system uses a camera and YOLOv8 to detect pedestrians and vehicles, understand their position within the road scene, estimate collision risk, and make basic driving decisions such as braking or steering.

The prototype was deployed on an **NVIDIA Jetson Nano**, which was used as the onboard computing platform for the perception and decision-making pipeline.

---

## What This Project Does

The system takes a live camera feed and processes it in real time to:

- Detect pedestrians and vehicles using YOLOv8
- Classify detected objects
- Assign objects to left, center, or right road zones
- Estimate approximate object distance from bounding-box size
- Estimate collision risk from changes in object size over time
- Classify the current situation as `SAFE`, `WARNING`, or `CRITICAL`
- Give pedestrians priority in the safety logic
- Make basic driving decisions such as:
  - Continue driving
  - Brake
  - Steer left
  - Steer right
- Calculate a basic steering command using a PD controller
- Display the vehicle state and safety information through an OpenCV dashboard

---

## System Pipeline

```text
Camera Feed
     ↓
YOLOv8 Object Detection
     ↓
Object Classification
     ↓
Lane-Zone Assignment
     ↓
Distance & Collision-Risk Estimation
     ↓
Risk Classification
     ↓
Decision Logic
     ↓
Brake / Steering Command
     ↓
Real-Time Dashboard
```

---

## Hardware

### NVIDIA Jetson Nano

The Jetson Nano was used as the onboard computing platform for the prototype.

It handled the computer vision and decision-making pipeline while receiving input from the camera.

The larger project was designed around an autonomous drive-by-wire vehicle architecture, where the perception and decision layer would ultimately interact with the vehicle control and actuation system.

---

## Technologies Used

* Python
* OpenCV
* YOLOv8
* Ultralytics
* NumPy
* NVIDIA Jetson Nano
* CUDA

---

## Object Detection

The perception pipeline uses the **YOLOv8** object detection model.

The prototype primarily considers the following objects:

| Object     | COCO Class |
| ---------- | ---------- |
| Person     | 0          |
| Car        | 2          |
| Motorcycle | 3          |
| Bus        | 5          |
| Truck      | 7          |

The implementation uses a confidence threshold of `0.5`.

---

## Lane-Zone Reasoning

The current prototype divides the camera view into three spatial zones:

```text
┌──────────┬──────────┬──────────┐
│   LEFT   │  CENTER  │  RIGHT   │
└──────────┴──────────┴──────────┘
```

Objects are assigned to a zone based on the horizontal center of their bounding box.

The system then uses the occupancy of these zones to make basic decisions.

For example:

```text
Center lane occupied
        ↓
   Check left
        ↓
 Left is clear?
    ↙       ↘
  YES        NO
   ↓          ↓
STEER LEFT   Check right
                ↓
            STEER RIGHT
```

This is a simplified lane representation rather than a dedicated lane-detection system.

---

## Collision Risk Estimation

The prototype uses the size of an object's bounding box as a rough indicator of its distance from the camera.

As an object approaches the camera, its bounding box generally becomes larger.

The change in bounding-box area over time is used to estimate a basic **Time-to-Collision (TTC) style metric**.

The estimate is smoothed across multiple frames before being used by the decision logic.

### Risk levels

| Risk     | Interpretation                |
| -------- | ------------------------------ |
| SAFE     | No immediate collision risk   |
| WARNING  | Increasing collision risk     |
| CRITICAL | High/immediate collision risk |

> **Note:** The current implementation uses a bounding-box growth heuristic. It is not a calibrated physical TTC measurement and would require proper tracking, calibration and/or additional sensors for a production system.

---

## Pedestrian Safety

Pedestrian detection has priority within the decision logic.

When a pedestrian is detected, the system can trigger a braking action:

```text
Pedestrian detected
        ↓
      BRAKE
        ↓
  Throttle → 0
```

A short detection-memory window is also used to prevent the system from immediately forgetting a pedestrian if detection is missed for a single frame.

---

## Steering Control

When the center zone is occupied, the system checks the available side zones and selects a clear direction when possible.

A simple **PD-style controller** is then used to calculate the steering command based on the desired lane center.

The steering value is constrained to a defined range before being displayed by the system.

---

## Real-Time Dashboard

The OpenCV interface displays information about the current state of the system, including:

* Vehicle speed
* Estimated TTC
* Risk level
* Lane occupancy
* Steering angle
* Brake status
* Throttle
* Current driving action

Example:

```text
ADAS SYSTEM

Speed: 40 km/h
TTC: 5.2 sec
Risk: WARNING

LANES:
L: CLEAR
C: VEHICLE
R: CLEAR

CONTROL:
Steering: -18 deg
Brake: OFF
Throttle: 50%

Action: STEER LEFT
```

---

## Running the Project

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/real-time-adas-perception.git
cd real-time-adas-perception
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the system

```bash
python adas_system.py
```

The program uses the connected camera as its input.

Press `ESC` to exit.

---

## My Contribution

I worked primarily on the software side of the project, focusing on the perception and decision-making pipeline.

My work included:

- Implementing the YOLOv8-based object detection pipeline
- Filtering relevant vehicle and pedestrian classes
- Developing the basic collision-risk and TTC-style estimation logic
- Implementing pedestrian detection and safety priority logic
- Developing the lane-zone based decision-making logic
- Implementing the PD-style steering control
- Building the real-time OpenCV dashboard for system feedback
- Working with the team on the deployment of the perception system on the NVIDIA Jetson Nano

The work involved connecting the perception output to simple driving decisions such as braking and steering, rather than treating object detection as a standalone computer vision task.

--- 

## Project Structure

```text
real-time-adas-perception/
│
├── adas_system.py
├── README.md
├── requirements.txt
├── .gitignore
├── LICENSE
│
├── docs/
│   ├── project-report.pdf
│   ├── presentation.pdf
│   └── conference-paper.pdf
│
└── assets/
    ├── detection-demo.png
    └── adas-dashboard.png
```

---

## Project Context

This project was developed as part of a larger academic project focused on an **autonomous drive-by-wire vehicle**.

The overall concept combined:

```text
Perception
    ↓
Decision Making
    ↓
Vehicle Control
    ↓
Drive-by-Wire Actuation
```

My work was primarily focused on the **software/perception and decision-making side**, including the YOLO-based detection pipeline, risk logic, lane-zone reasoning, pedestrian safety logic, and steering control.

The project also involved deployment on an **NVIDIA Jetson Nano** as the onboard computing platform.

---

## Results

The project documentation reports performance improvements through different stages of the system, including the transition from the lightweight YOLOv8n implementation to larger models and additional perception components.

The reported final system performance was approximately:

* **68% mAP**
* **22 FPS**

These results are based on the project team's documented experiments.

---

## Limitations

This repository represents an academic prototype rather than a production autonomous-driving system.

Some limitations of the current implementation include:

* Camera-based perception
* Approximate distance estimation
* Heuristic TTC estimation
* Simplified lane-zone representation
* Simplified vehicle dynamics
* Limited object association between frames
* No production-grade sensor fusion
* No safety validation for real-world autonomous driving

---

## Future Improvements

Potential extensions include:

* Dedicated lane detection
* Robust multi-object tracking
* Camera calibration and metric distance estimation
* LiDAR/RADAR integration
* Improved Time-to-Collision estimation
* Sensor fusion
* Hardware-in-the-loop testing
* TensorRT optimization
* Further deployment and optimization on NVIDIA Jetson platforms
* Complete integration with the physical drive-by-wire system

---

## Disclaimer

This project is an academic prototype developed for learning and experimentation in computer vision, ADAS, and autonomous vehicle systems.

It is **not intended for controlling a real vehicle or making safety-critical driving decisions**.

---

## License

This project is licensed under the MIT License.
