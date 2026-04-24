# 🤚 GestFlow
> **Grab anything on your screen. Throw it to another device. It continues from exactly where you left off. No touching. No cables. No setup. Just gestures.**

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Node.js](https://img.shields.io/badge/Node.js-18+-green?logo=node.js&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00?logo=tensorflow&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Status](https://img.shields.io/badge/Status-In_Development-orange)
![Student](https://img.shields.io/badge/Built_by-CS_Student-purple)

---

## 🎯 What Is GestFlow?

GestFlow is a **touchless, gesture-controlled cross-device content transfer system.**

Using only a standard webcam and hand gestures, you can:

- ✊ **Grab** a video playing on your laptop
- 👉 **Throw** it to another computer on the same network
- 🖐️ **Resume** it on the target device at the exact same timestamp

This works for **any content type:**

| Content | Gesture | What Happens |
|---------|---------|--------------|
| 🎬 Video | Fist grab → throw | Resumes at exact timestamp on target |
| 🎵 Music | Pinch → throw | Continues from same position + playlist |
| 💻 Code | Two-finger grab → throw | Opens at same file, same line, same branch |
| 🌐 Browser tab | Swipe | Opens same URL on target device |
| 📁 File / Folder | Fist → swipe | Opens in file manager on target |
| 📋 Text / Clipboard | Snap fingers | Pastes instantly on target |
| 🖼️ Image | Pinch → throw | Opens in image viewer on target |

No AirDrop. No Apple ecosystem lock-in. No expensive hardware. **Works across any brand, any OS, any device.**

---

## 💡 The Problem GestFlow Solves

Every existing solution has at least one of these frustrations:

- **Apple Handoff** — only works if you own all Apple devices
- **KDE Connect** — no gesture control, no state preservation
- **AirDrop** — just file transfer, no content resumption
- **Pushbullet / ShareDrop** — basic clipboard sync, nothing more
- **Leap Motion** — requires an $80 special hardware device

GestFlow's unique position:

```
Gesture controlled  +  Cross-brand  +  State preserved  +  Touchless  +  Free
```

Nobody else has all five. That is the gap GestFlow fills.

---

## ✋ Gesture Vocabulary

| Gesture | Hand Signal | Action |
|---------|-------------|--------|
| ✊ | Close fist | SELECT / GRAB item on screen |
| 🖐️ | Open hand | PASTE / RELEASE on target device |
| 👉 | Point + swipe right | THROW to device on the right |
| 👈 | Point + swipe left | THROW to device on the left |
| 🤏 | Pinch fingers | GRAB small item (text, link, image) |
| ✌️ | Two fingers up | SELECT multiple items |
| 👆 | Point upward | SEND to ALL connected devices |
| 🤙 | Shake hand | CANCEL / UNDO last action |
| 🖖 | Spread all fingers | OPEN / EXPAND item on screen |
| 🔄 | Rotate hand | ROTATE / TRANSFORM item |

---

## 🏗️ How It Works — System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        DEVICE A                         │
│                                                         │
│  [Camera] → [OpenCV] → [MediaPipe CNN] → [Landmarks]   │
│                                ↓                        │
│                    [Gesture Classifier]                 │
│                    (TensorFlow model)                   │
│                                ↓                        │
│                    [Content Detector]                   │
│                    (OS Accessibility API)               │
│                                ↓                        │
│                    [State Capture]                      │
│                    (timestamp, file, cursor, branch)    │
│                                ↓                        │
│                    [Transfer Engine]                    │
│                    (WebSockets + mDNS)                  │
└────────────────────────────┬────────────────────────────┘
                             │ Wi-Fi (same network)
                             ↓
┌─────────────────────────────────────────────────────────┐
│                        DEVICE B                         │
│                                                         │
│                    [Receiver Engine]                    │
│                                ↓                        │
│                    [App Launcher]                       │
│                    (opens correct app)                  │
│                                ↓                        │
│                    [State Injector]                     │
│                    (seeks to timestamp, opens line)     │
│                                ↓                        │
│              [Content resumes seamlessly] ✅            │
└─────────────────────────────────────────────────────────┘
```

---

## 🗺️ Development Roadmap

This repo is organized by phases. Each phase has its own folder containing both **learning notes** and **working code.**

---

### Phase 1 — Gesture Engine `📁 phase-1-gesture-engine/`
**Status:** 🟡 In Progress
**Duration:** 4–6 weeks

The foundation of everything. Learn computer vision from scratch and build a working hand gesture recognition system using only a webcam.

**What I learn in this phase:**
- OpenCV — camera feed, frame processing, drawing, color conversion
- MediaPipe Hands — 21 landmark detection, coordinate system, real-time tracking
- TensorFlow — build and train a custom gesture classifier on top of landmarks
- Data collection — record my own gesture training samples
- Model evaluation — accuracy, confusion matrix, real-world testing

**Key files:**
```
phase-1-gesture-engine/
├── 01_opencv_basics/
│   ├── camera_feed.py          ← open and display camera
│   ├── drawing.py              ← draw shapes and text on frames
│   ├── colors.py               ← BGR vs RGB conversion
│   └── gestflow_base.py        ← final camera shell for GestFlow
├── 02_mediapipe/
│   ├── hand_tracking.py        ← detect hand and draw landmarks
│   ├── landmark_explorer.py    ← understand all 21 points
│   └── hand_geometry.py        ← calculate distances and angles
├── 03_gesture_classifier/
│   ├── data_collector.py       ← record training samples
│   ├── train_model.py          ← train TensorFlow classifier
│   ├── evaluate_model.py       ← test accuracy
│   └── live_demo.py            ← real-time gesture detection
└── models/
    └── gesture_model.tflite    ← trained model
```

**Milestone:** Live demo showing 10 gestures recognized in real time with 95%+ accuracy

---

### Phase 2 — Content Grabber `📁 phase-2-content-grabber/`
**Status:** ⬜ Not Started
**Duration:** 3–4 weeks

Teach GestFlow to know what is on screen under your hand so it knows what to grab.

**What I learn in this phase:**
- OS Accessibility APIs — Windows UI Automation, macOS AX API, Linux xdotool
- Process detection — identify active app using psutil
- App-specific adapters — VLC, Chrome, Spotify, VSCode, File Explorer
- Content type classification — video, audio, code, browser, file

**Key files:**
```
phase-2-content-grabber/
├── screen_reader.py            ← detect active app and content
├── content_classifier.py       ← identify content type
└── adapters/
    ├── vlc_adapter.py          ← read VLC state
    ├── chrome_adapter.py       ← read Chrome tab
    ├── spotify_adapter.py      ← read Spotify state
    ├── vscode_adapter.py       ← read VSCode state
    └── file_adapter.py         ← read file manager state
```

**Milestone:** App correctly identifies whether you are grabbing a video, code file, browser tab, or music

---

### Phase 3 — State Capture `📁 phase-3-state-capture/`
**Status:** ⬜ Not Started
**Duration:** 3–4 weeks

Capture the complete state of any content at the exact moment of the grab gesture so it can be perfectly resumed on another device.

**What I learn in this phase:**
- VLC Python bindings — read timestamp, volume, subtitle track
- Spotify Web API — read playback position, playlist state
- Chrome DevTools Protocol — read URL, scroll position
- VSCode Extension API — read open file, cursor line, git branch
- JSON state serialization — design portable state packet format

**Key files:**
```
phase-3-state-capture/
├── state_schema.py             ← defines portable state JSON format
├── video_state.py              ← capture VLC/media player state
├── audio_state.py              ← capture Spotify/music state
├── code_state.py               ← capture VSCode state
├── browser_state.py            ← capture Chrome state
└── tests/
    └── state_accuracy_tests.py ← verify state is captured correctly
```

**Milestone:** Grab a video and print a JSON packet showing exact file path, timestamp, volume, and subtitle track

---

### Phase 4 — Transfer Protocol `📁 phase-4-transfer-protocol/`
**Status:** ⬜ Not Started
**Duration:** 4–5 weeks

Build the networking layer that makes devices discover each other automatically and transfer content securely over Wi-Fi.

**What I learn in this phase:**
- mDNS / Zeroconf — automatic device discovery without configuration
- WebSockets — real-time bidirectional communication between devices
- asyncio — asynchronous Python for handling multiple connections
- TLS / SSL — encrypt transfers so content is secure
- Heartbeat systems — keep devices aware of each other continuously

**Key files:**
```
phase-4-transfer-protocol/
├── discovery/
│   ├── broadcaster.py          ← announce device on network
│   └── scanner.py              ← find other GestFlow devices
├── server/
│   ├── transfer_server.js      ← Node.js WebSocket server
│   └── transfer_client.py      ← Python client for sending
├── security/
│   └── encryption.py           ← TLS transfer encryption
└── tests/
    └── network_tests.py        ← test discovery and transfer speed
```

**Milestone:** Two laptops on same Wi-Fi find each other automatically and transfer a JSON state packet in under 100ms

---

### Phase 5 — Receiver Engine `📁 phase-5-receiver-engine/`
**Status:** ⬜ Not Started
**Duration:** 3–4 weeks

Build the target device side — receive the state packet, open the right app, and resume content from exactly where it was.

**What I learn in this phase:**
- App launching — open correct app for each content type programmatically
- State injection — seek VLC to timestamp, open VSCode at specific line
- Chrome DevTools Protocol — open URL and restore scroll position
- Spotify API — resume playback at exact position
- End-to-end testing — full throw and resume flow between two machines

**Key files:**
```
phase-5-receiver-engine/
├── receiver_daemon.py          ← listens for incoming transfers
├── app_launcher.py             ← opens correct app for content type
└── injectors/
    ├── video_injector.py       ← seek VLC to timestamp
    ├── audio_injector.py       ← resume Spotify at position
    ├── code_injector.py        ← open VSCode at file and line
    └── browser_injector.py     ← open Chrome at URL
```

**Milestone:** Full end-to-end demo — grab playing video on laptop A using fist gesture, open hand on laptop B, video resumes at exact same second ✅

---

### Phase 6 — Polish, Package, Mobile `📁 phase-6-polish-and-mobile/`
**Status:** ⬜ Not Started
**Duration:** 6–8 weeks

Package the full system into a real installable product, add Android support, and prepare for public release.

**What I learn in this phase:**
- Electron / Tauri — wrap Python + Node.js app into a desktop application
- electron-builder — create installers for Windows, Mac, Linux
- Flutter — build Android app for mobile gesture detection
- CI/CD with GitHub Actions — automated testing and deployment pipeline
- User research — beta testing, feedback loops, iteration

**Key files:**
```
phase-6-polish-and-mobile/
├── desktop-app/
│   ├── main.js                 ← Electron entry point
│   ├── src/                    ← React + Tailwind UI
│   └── electron-builder.json   ← packaging config
├── android-app/
│   └── lib/                    ← Flutter app source
└── .github/
    └── workflows/
        └── ci.yml              ← GitHub Actions pipeline
```

**Milestone:** GestFlow installer that runs on any laptop + Android APK available for download

---

## 🛠️ Full Technology Stack

| Layer | Technology | Why |
|-------|------------|-----|
| Computer Vision | OpenCV | Camera capture and frame processing |
| Hand Tracking | MediaPipe Hands (Google) | 21 landmark detection in real time |
| Gesture Classification | TensorFlow Lite | Lightweight model running on CPU |
| Backend Transfer | Node.js + WebSockets | Real-time cross-device communication |
| Device Discovery | python-zeroconf (mDNS) | Automatic zero-config device detection |
| State Capture | VLC API, Spotify API, Chrome DevTools | Read content state from apps |
| Desktop UI | React + Tailwind CSS | Settings panel and device manager |
| Desktop Packaging | Electron / Tauri | Cross-platform installer |
| Mobile App | Flutter | Android gesture detection |
| Containerization | Docker + Kubernetes | Deployment and scaling |
| Cloud Relay | AWS / GCP | Long-distance transfer (optional) |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Encryption | TLS / SSL | Secure content transfer |

---

## ⚙️ Setup and Installation

### Prerequisites
- Python 3.8+
- Node.js 18+
- A webcam
- Ubuntu / Debian / Mac / Windows

### Clone and setup
```bash
git clone https://github.com/YOUR_USERNAME/gestflow.git
cd gestflow

# Create virtual environment
python3 -m venv gestflow-env
source gestflow-env/bin/activate  # Linux/Mac

# Install Python dependencies
pip install opencv-python mediapipe tensorflow numpy websockets zeroconf

# Install Node.js dependencies
npm install
```

### Run Phase 1 demo
```bash
cd phase-1-gesture-engine/01_opencv_basics
python3 camera_feed.py
# Press Q to quit
```

---

## 📊 Progress Tracker

| Phase | Topic | Status | Completion |
|-------|-------|--------|------------|
| 1 | Gesture Engine | 🟡 In Progress | 0% |
| 2 | Content Grabber | ⬜ Not Started | 0% |
| 3 | State Capture | ⬜ Not Started | 0% |
| 4 | Transfer Protocol | ⬜ Not Started | 0% |
| 5 | Receiver Engine | ⬜ Not Started | 0% |
| 6 | Polish + Mobile | ⬜ Not Started | 0% |

> ⬜ Not started &nbsp;&nbsp; 🟡 In progress &nbsp;&nbsp; ✅ Complete

---

## 🧠 Learning Notes

Personal notes, discoveries, and lessons learned during each phase are documented in:

```
notes/
├── phase-1-opencv-mediapipe.md
├── phase-2-os-apis.md
├── phase-3-state-capture.md
├── phase-4-networking.md
├── phase-5-receiver.md
└── phase-6-packaging.md
```

---

## 🔭 Future Vision

Once the core product works, GestFlow can expand into:

- **Hospital / Medical** — touchless control for surgeons in sterile environments
- **Smart home** — control TV, lights, and devices with gestures
- **Accessibility** — life-changing for people with limited mobility
- **Enterprise** — gesture-controlled presentations and meeting room displays
- **AR / VR integration** — natural input layer for spatial computing

---

## 👤 About The Builder

Third year Computer Science student passionate about building tools that change how people interact with technology.

**Skills:** Python · Django · Node.js · React · Tailwind · TensorFlow · OpenCV · Docker · Kubernetes · AWS · GCP · CI/CD · Algorithm Design

**Goal:** Build GestFlow from scratch as both a deep learning exercise and a real product with genuine commercial potential.

---

## 📄 License

MIT License — free to use, learn from, and build on.

---

<p align="center">
  <i>Built one gesture at a time. 🤚</i>
</p>
