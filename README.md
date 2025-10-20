# 🛰️CubeSat Attitude Control System 🚀

## ✨ Project Overview

This repository contains the **simulation environment** and **mission control software** for a CubeSat Attitude Control System (ACS). The primary objective of this project is to provide a comprehensive tool for visualizing and controlling a satellite's orbit. The system uses a simulated **PID controller** to maintain a stable orbital trajectory, which is crucial for missions such as Earth imaging, scientific data collection, or telecommunications.

## 👨‍💻Project Members
- **Dinith Madushan**
- **Savindu Dabarera**
- **Thilina Sandaruwan**
- **Gimsara Pieris**
- **Imaya Ranaweera**
- **Thamashi Nanayakkara**

## 💡 Key Features

- **Orbital Simulation**: Real-time 3D simulation of a satellite's orbit using a custom physics model. 🚀
- **PID Control**: A Proportional-Integral-Derivative (PID) controller automatically adjusts the satellite's orbital parameters (Altitude, Inclination, and Eccentricity) to keep it on its target course. 🎯
- **Telemetry Dashboard**: A dashboard displays live telemetry data, including altitude, inclination, and eccentricity. 📊
- **Historical Data**: Records and plots historical data of satellite drift and corrections, providing insights into system performance. 📈
- **User Authentication**: A simple login page for secure access to the mission control interface. 🔒

---

## 🏗️ Codebase Architecture and Component Explanation

The application is structured into several modular Python files, promoting clear separation of concerns:

| File Name | Role in the System | Key Components and Functionality |
| :--- | :--- | :--- |
| **`main.py`** | **Application Entry & Core Loop** | Initializes the entire system (GUI, satellite, PID controller, sensor, and telemetry) and manages the main **real-time simulation loop** using a separate thread. |
| **`config.py`** | **Central Configuration** | Stores all critical system constants, including **Target Orbital Parameters** (`TARGET_ALTITUDE`, `TARGET_INCLINATION`, etc.), **PID Gains** (`PID_GAINS`), and GUI theme settings.⚙️ |
| **`satellite_components.py`** | **The Satellite Model** | Contains the `Satellite` class (the physics model), which tracks orbital parameters, applies simulated **orbital drift**, and executes the `apply_orbital_correction` based on PID output. Also includes the `Sensor` class for noisy telemetry data. |
| **`control_algorithm.py`** | **The Control Logic** | Implements the core **`PIDController`** class. It calculates a 3D correction vector based on the difference between the target orbital state and the current sensed orbital state, using NumPy for efficient vector arithmetic. |
| **`orbit_simulation.py`** | **3D Visualizer** | Manages the `OrbitSimulationFrame`, which uses Matplotlib to generate the **real-time 3D visualization** of the Earth and the satellite's current trajectory based on its orbital parameters.🌐 |
| **`telemetry.py`** | **Data Management** | The `TelemetrySystem` class stores all live and historical data (orbital state, corrections, etc.) in fixed-size `deque` structures to manage memory usage efficiently. |
| **`history.py`** | **Event Logging** | The `HistoryRecorder` logs significant events, such as when the satellite drifts and when a correction is made, for later analysis.📝 |
| **`login.py`** | **User Interface (Login)** | Handles the initial authentication screen, using CustomTkinter and PIL for image management. |

---

## 📸 Application Screenshots and Features

### 1. User Authentication (login.py)
<div align="center">
      
<img src ="Images\login.png" alt = "loginscreen" width = "400"/>
      
 *Secure Login Interface*
  
</div>

The application starts with a secure login page. This component ensures that only authorized personnel can access the mission control dashboard.



### 2. Main Dashboard
<div align="center">
      
<img src ="Images\dashboard.png" alt = "System Dashboard" width = "400"/>
      
 *Mission Control Dashboard Overview*
  
</div>

The central hub for mission control. It displays real-time key metrics and controls the simulation.



### 3. Real-Time Orbital Simulation (orbit_simulation.py)
<div align="center">
      
<img src ="Images\orbit sim.png" alt = "Orbit simulation" width = "400"/>
      
 *Dynamic 3D Orbit Simulator*
  
</div>

The `OrbitSimulationFrame` provides a dynamic 3D view of the CubeSat's orbit. The orbit path and satellite position are updated live based on the current `altitude`, `inclination`, and `eccentricity` values from the `Satellite` object.



### 4. Historical Data and Telemetry Plots
<div align="center">
      
<img src ="Images\plots.png" alt = "Data plots" width = "400"/>
      
 *Orbital Drift and Correction Plots*
  
</div>

The application includes a section to visualize the performance of the PID controller. These plots show the satellite's drift over time and the magnitude of the corrections applied by the controller.



---

## 🛠️ Technologies Used

- **Python 🐍**: The core programming language for the application.
- **CustomTkinter**: Used for building a dependable and modern graphical user interface.
- **Matplotlib**: Generates real-time plots of orbital data and historical logs.
- **NumPy**: Provides efficient numerical and mathematical operations for computation algorithms (specifically the PID controller) and simulations.
- **Threading**: Enables the real-time simulation and GUI to run concurrently without freezing the application.

## ▶️ How to Run the Application

1. **Prerequisites**
      - Ensure you have **Python 3.7 or newer** installed.

2. **Install Dependencies**
      Open your terminal or command prompt and install the required libraries using pip:

       pip install customtkinter matplotlib numpy pillow


3. **Run the Application**
 - Navigate to the project directory and run the main application file:

         python main.py


  - The application will first display a login window. Use the default credentials:

    - ◻ 🔑**Username**: admin
    - ◻ 🔐**Password**: password

⭐️ Upon successful login, the main mission control dashboard will appear, and the orbital simulation will begin.
