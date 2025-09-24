# CubeSat Attitude Control System 🛰️
## Project Overview
This repository contains the simulation environment and mission control software for a CubeSat Attitude Control System (ACS). The primary objective of this project is to provide a comprehensive tool for visualizing and controlling a satellite's orbit. The system uses a simulated PID controller to maintain a stable orbital trajectory, which is crucial for missions such as Earth imaging, scientific data collection, or telecommunications.

## Project Members👨‍💻
- **Dinith**

- **Savindu**

- **Thilina**

- **Gimsara**

- **Imaya**

- **Thamashi**

## Features
- Orbital Simulation: Real-time 3D simulation of a satellite's orbit using a custom physics model. 🚀

- PID Control: A Proportional-Integral-Derivative (PID) controller automatically adjusts the satellite's altitude to keep it on its target course. 🎯

- Telemetry Dashboard: A dashboard displays live telemetry data, including altitude, inclination, and eccentricity. 📊

- Historical Data: Records and plots historical data of satellite drift and corrections, providing insights into system performance. 📈

- User Authentication: A simple login page for secure access to the mission control interface. 🔒

## Technologies Used
- Python: The core programming language for the application.

- CustomTkinter: Used for building dependable  and modern graphical user interface.

- Matplotlib: Generates real-time plots of orbital data and historical logs.

- NumPy: Provides efficient numerical and mathematical operations for computation algorithms and simulations.

- Threading: Enables the real-time simulation and GUI to run concurrently without freezing the application.

## How to Run the Application
1. **Prerequisites**
      - Ensure you have Python 3.7 or newer installed.

2. **Install Dependencies**
      Open your terminal or command prompt and install the required libraries using pip:

       pip install customtkinter matplotlib numpy


3. **Run the Application**
 - Navigate to the project directory and run the main application file:

         python main.py


  - The application will first display a login window. Use the default credentials:

    ◻ Username: admin

    ◻ Password: password

⭐️Upon successful login, the main mission control dashboard will appear, and the orbital simulation will begin.