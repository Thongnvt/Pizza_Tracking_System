# Pizza Box Tracker – Smart Detection & State Management System

An intelligent vision-based system to automatically detect, track, and count pizza boxes sold based on their open/close status, location, and status transitions.

## 📌 Objective

The goal of this project is to automate pizza sale counting through:

-   Detecting the open/close status of pizza boxes.
-   Verifying if a box is within the delivery area (ROI).
-   Assigning unique IDs and managing the state history for each box.

## 🎯 System Workflow

1.  **Detection**: YOLOv8 detects pizza boxes and classifies them as "open" or "close".
2.  **Tracking**: DeepSORT or ByteTrack assigns a unique ID to each detected box.
3.  **ROI Check**: Determine if a box is within the defined delivery area.
4.  **State Management**: Track the history of status changes for each box.
5.  **Sold Condition**: Apply logic rules to determine if a box has been sold.

## ✅ State Transition Rules

A box is considered "Sold" if it transitions through certain status sequences:

| Box ID | Observed Status History | Final Status |
| :----- | :---------------------- | :----------- |
| 01     | `["open", "close"]`   | ✅ Sold      |
| 02     | `["close", "open", "close"]` | ✅ Sold      |
| 03     | `["open"]` or `["close"]` | ⏳ Pending   |

## 🔁 Update Logic

-   When a new box appears → Add to `array_pending`.
-   When a box meets the sold condition → Move it to `array_sold`.

## 🧾 Output (Real-time or Post-processing)

-   `array_pending`: Boxes currently being monitored.
-   `array_sold`: Boxes confirmed as sold.

## 🧠 System Components

-   **Frontend**: A React web app for UI and visualization.
-   **Backend**: A Flask-based server handling logic, tracking, and state updates.
-   **Database**: MongoDB stores tracking history, feedback, and state data.
-   **Tracking**: Based on DeepSORT or SFSORT (with Kalman Filter).



## ⚙️ Training Method

To train the YOLOv11 model for pizza box detection, the following workflow was used:

1.  **Data Preparation**: Video footage was used to extract individual frames. These frames were then manually labeled using `labelImg` to create the necessary annotations for object detection.

2.  **Dataset Organization**: The labeled data was organized into a `data_process` folder, following the specific structure required for YOLOv11 model training. This folder includes:

    -   `images/`: Contains the image files.
    -   `labels/`: Contains the corresponding annotation files.
    -   `best.pt`: The trained model weights.
    -   `classes`: A text file listing the object classes.
    -   `data`: A YAML file defining the dataset configuration.

           ```
        label/
        ├── images/               
        │   ├── test/        
        │   ├── train/
        │   └── val/
        │
        ├── labels/              
        │   ├── test/
        │   ├── train/
        │   └── val/
        │
        ├── classes.txt
        └── data.yaml
        ```

4.  **Dataset Split**: The dataset for training consisted of 1080 image files. These were split into training, validation, and testing sets with an 8:1:1 ratio, with 8 in train, 1 in vali and 1 in test.

5.  **Training Results**: The training process yielded the following performance metrics, demonstrating the model's learning progress and accuracy:

    ![Training Metrics]![a991f9da-0928-481a-a982-9a60cdde6043](https://github.com/user-attachments/assets/963c1985-4ceb-4765-88e3-f1343b0e8636)


6. **Data Folder**: https://drive.google.com/drive/u/2/folders/1FxAHPU5ll0oOJy7D6Evk117-LW-E1PvB
   


## 🗂️ Project Structure

```
pizza-tracker/
├── backend/               # Flask server, model inference, API
│   ├── app.py             # Backend entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── utils/             # Detection, tracking, ROI logic
│
├── frontend/              # React UI
│   ├── src/
│   └── Dockerfile
│
├── db/                    # MongoDB data (feedback, state)
├── SFSORT/                # Tracking logic with Kalman Filter
├── train/                 # Model training scripts
├── main.py                # GUI-based execution entry point
├── docker-compose.yml     # Docker service definitions
└── README.md              # Project documentation
```

## 🚀 Getting Started

You can run the project in three ways (Please connect with mongoDB localhost:27017 for feedback interface):

### ✅ Option 1: With GUI (Tkinter)

```bash
python main.py
```

### ✅ Option 2: Manual Run (Frontend + Backend)

Split your terminal into two.

**Run the backend:**

```bash
cd backend
python app.py
```

**Run the frontend:**

```bash
cd frontend/src/components
npm start
```

### ✅ Option 3: Using Docker Compose

**Step 1: Clone the Repository**

```bash
git clone https://github.com/Thongnvt/Pizza_Tracking_System.git
cd Pizza_Tracking_System
```

**Step 2: Build & Run with Docker**

```bash
docker-compose up --build
```

You can skip `--build` if images are already built and unchanged.

**Step 3: Access the App**

-   **Frontend**: `http://localhost:3000`
-   **Backend API**: `http://localhost:5000`
-   **MongoDB**: internal access via port `27017`

### Stopping the Services

```bash
docker-compose down      # Stops and removes everything
docker-compose stop      # Stops containers but keeps them
```

## 📦 Dependencies

### 🔹 Backend (Python)

From `requirements.txt`:

-   `flask`, `flask-cors`, `flask-socketio`, `werkzeug`
-   `numpy`, `opencv-python`, `matplotlib`, `pillow`
-   `filterpy`, `lap`, `scipy`, `shapely`, `torch`, `ultralytics`
-   `pymongo`, `requests`

### 🔹 Frontend (React/Node.js)

Handled via `package.json`, includes:

-   `react`, `axios`, `socket.io-client`, etc.

## 🌟 Potential Extensions

-   Integrate Reinforcement Learning to optimize detection strategies or ROI zones.
-   Enable Active Learning via user feedback from the frontend.
-   Add anomaly alerts, e.g., boxes opened but not closed.

## 🤝 Contributing

Pull requests and feedback are welcome. Please open issues for any bugs or suggestions.

## 📄 License

This project is open-source and licensed under the MIT License.






