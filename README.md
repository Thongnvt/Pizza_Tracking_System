 Pizza Box Tracker – Smart Detection & State Management System

 Objective: 

Build an automated system to count the number of pizzas sold over a given time period based on:

+ The open/close status of the pizza box.

+ The position of the pizza box within the delivery area 

+ ID assignment and state management for each box

  Overall Processing Flow: 

+ YOLOv8 detects pizza boxes and their status (open or close).

+ Tracking (DeepSORT/ByteTrack) assigns a unique ID to each box.

+ Determine whether the box is inside the ROI area.

+ Record the status over time for each box by ID.

+ Apply state transition rules to determine if a box has been "sold".

Rules for Determining a Box as Sold: 

![Screenshot 2025-06-18 181833](https://github.com/user-attachments/assets/d5072a60-17c9-43d6-9625-6d05b5bbeecf)
![Screenshot 2025-06-18 181833](https://github.com/user-attachments/assets/d5072a60-17c9-43d6-9625-6d05b5bbeecf)

Update Flow: 

+ When a new box appears → add to array_pending.

+ When the status sequence meets the "sold" criteria → move from pending to sold.

Output (Real-time or Post-video):

+ array_pending: list of box IDs awaiting completion.

+ array_sold: list of box IDs marked as sold.

System Overview

The system is composed of two main services:

•
Frontend: A web application built with React that provides the user interface.

•
Backend: A Flask-based API that handles data processing, interacts with the MongoDB database, and likely incorporates the Activate Learning and Reinforcement Learning components.

•
MongoDB: A NoSQL database used to store application data.

How it Works

1.
Data Collection: The system tracks pizza sales data.

2.
Backend Processing: The backend processes this data, potentially applying machine learning models for feedback and learning.

3.
Frontend Display: The frontend visualizes the processed data and provides an interface for user interaction and feedback.

4.
Database: MongoDB stores all the necessary data for the application.

Getting Started

To run this project, there are 3 options of running: with Docker Composer, run frontend local and run with GUI tkinter 

With GUI tkinter: 

run python main.py 

With localhost: 

•
Split the terminal in half

• 
Then run: cd backend/python app.py to activate backend server. 

• 
Then run: cd frontend/src/components/npm start to start frontend.




Prerequisites

•
Docker

•
Docker Compose

Running with Docker Compose

1.
Clone the repository:

2.
Build and run the services:

•
--build: This flag ensures that Docker images for the frontend and backend services are built from their respective Dockerfiles before starting the containers. If you have already built the images and haven't made changes to the Dockerfiles or dependencies, you can omit this flag for faster startup.



3.
Access the application:

•
Frontend: Once the services are up, the frontend application should be accessible in your web browser at http://localhost:3000.

•
Backend API: The backend API will be running on http://localhost:5000.

•
MongoDB: The MongoDB database will be accessible internally within the Docker network on port 27017.



Stopping the services

To stop and remove the containers, networks, and volumes created by docker-compose up, run:

Bash


docker-compose down


To stop the services but keep the containers running (e.g., to restart them later), use:

Bash


docker-compose stop


Project Structure

•
backend/: Contains the core AI function, Flask backend application and its Dockerfile.

•
Dockerfile: Defines the Python environment and dependencies for the backend.

•
requirements.txt: Lists Python dependencies for the backend.

•
utils/: Core AI utilities use for detect and tracking. 





•
frontend/: Contains the React frontend application and its Dockerfile.

•
Dockerfile: Defines the Node.js environment and build process for the frontend.



•
docker-compose.yml: Defines the multi-container Docker application, including the frontend, backend, and MongoDB services.

•
db/: Contain database of user feedback.

•
SFSORT/: contain the tracking system, using SFSORT combine with Kalman Filter.
•

train/: Code using for training model

•
main.py: The entry point to run local with GUI tkinter.

Dependencies

Backend (Python)

Key dependencies from requirements.txt:

•
flask

•
flask-cors

•
flask-socketio

•
werkzeug

•
numpy

•
opencv-python

•
filterpy

•
lap

•
scipy

•
matplotlib

•
pillow

•
pymongo

•
shapely

•
torch

•
ultralytics

•
requests

Frontend (Node.js/React)

Dependencies are managed via package.json and package-lock.json.


How to run: 






