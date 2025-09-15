"""
main.py

Main application for the CubeSat Mission Control GUI.
Integrates all modules into a single interface.
Optimized for performance, maintainability, and best practices.
"""
import sys
import time
import datetime
import threading
from tkinter import END, scrolledtext
from collections import deque
import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --- Import custom modules ---
from satellite_components import Satellite, Thruster, Sensor
from control_algorithm import PIDController
from telemetry import TelemetrySystem
from history import HistoryRecorder
from orbit_simulation import OrbitSimulationFrame
from login import LoginPage

# --- Import centralized configuration ---
import config

class SatelliteGUI(ctk.CTkToplevel):
    """
    Main application window for the satellite control system GUI.
    This is a Toplevel window, meant to appear after the login.
    """
    def __init__(self, master: ctk.CTk, target_location: tuple):
        super().__init__(master)
        self.login_root = master  # Keep a reference to the root login window

        # --- System Initialization ---
        self.my_satellite = Satellite(target_location)
        self.my_thruster = Thruster()
        self.my_sensor = Sensor(self.my_satellite)
        self.my_telemetry = TelemetrySystem(max_log_size=config.TELEMETRY_LOG_MAX_SIZE)
        self.my_history = HistoryRecorder(max_history_size=config.HISTORY_LOG_MAX_SIZE)
        self.my_controller = PIDController(**config.PID_GAINS)

        # --- Simulation State ---
        self.loop_is_running = False
        self.recording_history = False
        self.loop_thread = None
        self.paused = True
        self.status_text = "Paused"

        # --- OPTIMIZATION: Use deques for plot data to cap memory usage ---
        self.drift_data = deque(maxlen=config.PLOT_DATA_MAX_POINTS)
        self.correction_counts = deque(maxlen=config.PLOT_DATA_MAX_POINTS)

        self._setup_gui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_gui(self) -> None:
        """Initializes the main GUI window and its components."""
        self.title("CubeSat Mission Control")
        self.geometry("1600x900")
        self.minsize(1200, 700)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Frame for Controls ---
        top_frame = ctk.CTkFrame(self, corner_radius=10)
        top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        self._setup_controls(top_frame)

        # --- Left Frame for Telemetry and History ---
        left_frame = ctk.CTkFrame(self, corner_radius=10)
        left_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        left_frame.grid_rowconfigure(1, weight=1)
        left_frame.grid_rowconfigure(3, weight=1)
        self._setup_telemetry_history(left_frame)

        # --- Right Frame for Plots and Orbit Sim ---
        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        right_frame.grid_rowconfigure(0, weight=1) # Make orbit sim expand
        self._setup_plots_and_orbit(right_frame)

    def _setup_controls(self, parent: ctk.CTkFrame) -> None:
        """Sets up the control buttons in the top frame."""
        parent.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)
        self.start_button = ctk.CTkButton(parent, text="Start Loop", command=self.toggle_loop)
        self.start_button.grid(row=0, column=0, padx=5, pady=10)
        self.pause_button = ctk.CTkButton(parent, text="Pause", command=self.toggle_pause)
        self.pause_button.grid(row=0, column=1, padx=5, pady=10)
        self.history_button = ctk.CTkButton(parent, text="Start Recording History", command=self.toggle_history_recording)
        self.history_button.grid(row=0, column=2, padx=5, pady=10)
        self.clear_history_button = ctk.CTkButton(parent, text="Clear History", command=self.clear_history,
                                                  fg_color=config.DANGER_COLOR, hover_color=config.DANGER_HOVER_COLOR)
        self.clear_history_button.grid(row=0, column=3, padx=5, pady=10)
        self.status_label = ctk.CTkLabel(parent, text=f"Status: {self.status_text}", font=("Roboto", 16))
        self.status_label.grid(row=0, column=4, padx=10, pady=10)

    def _setup_telemetry_history(self, parent: ctk.CTkFrame) -> None:
        """Sets up telemetry and history display areas."""
        parent.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(parent, text="Telemetry Data", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=5)
        self.telemetry_text = scrolledtext.ScrolledText(parent, wrap='word', height=10, bg="#2b2b2b", fg="white", bd=0)
        self.telemetry_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        ctk.CTkLabel(parent, text="Drift History", font=("Roboto", 16, "bold")).grid(row=2, column=0, pady=5)
        self.history_text = scrolledtext.ScrolledText(parent, wrap='word', height=10, bg="#2b2b2b", fg="white", bd=0)
        self.history_text.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")

    def _setup_plots_and_orbit(self, parent: ctk.CTkFrame) -> None:
        """Sets up the plots and the orbit simulation frame."""
        # --- Tab View for switching between plots and orbit sim ---
        tab_view = ctk.CTkTabview(parent)
        tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        plots_tab = tab_view.add("Live Plots")
        orbit_tab = tab_view.add("Orbit Simulation")

        # --- Live Plots ---
        plots_tab.grid_columnconfigure(0, weight=1)
        plots_tab.grid_rowconfigure((0, 1), weight=1)
        self.fig_corr, self.ax_corr = self._create_plot_figure("Correction Count Over Time")
        self.ax_corr.set_xlabel("Simulation Ticks", color='white')
        self.ax_corr.set_ylabel("Total Corrections", color='white')
        self.line_corr, = self.ax_corr.plot([], [], marker='o', color=config.CORRECTION_PLOT_COLOR)
        self.fig_corr.tight_layout() # Adjust layout AFTER adding labels
        self.canvas_corr = self.embed_plot(self.fig_corr, plots_tab, 0)

        self.fig_drift, self.ax_drift = self._create_plot_figure("Orbital Drift Over Time")
        self.ax_drift.set_xlabel("Simulation Ticks", color='white')
        self.ax_drift.set_ylabel("Error Magnitude (km)", color='white')
        self.line_drift, = self.ax_drift.plot([], [], marker='o', color=config.DRIFT_PLOT_COLOR)
        self.fig_drift.tight_layout() # Adjust layout AFTER adding labels
        self.canvas_drift = self.embed_plot(self.fig_drift, plots_tab, 1)

        # --- Orbit Simulation ---
        orbit_sim_frame = OrbitSimulationFrame(orbit_tab, fg_color="transparent")
        orbit_sim_frame.pack(fill="both", expand=True)

    def _create_plot_figure(self, title: str) -> tuple:
        """Helper to create a styled matplotlib Figure and Axes."""
        fig = plt.Figure(figsize=(8, 4), facecolor=config.PLOT_BG_COLOR)
        ax = fig.add_subplot(111, facecolor=config.PLOT_BG_COLOR)
        ax.set_title(title, color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
        # The tight_layout call is removed from here to be called after labels are set
        return fig, ax

    def embed_plot(self, fig: plt.Figure, parent: ctk.CTkFrame, row: int) -> FigureCanvasTkAgg:
        """Embeds a matplotlib figure into the Tkinter parent."""
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.get_tk_widget().grid(row=row, column=0, padx=10, pady=10, sticky="nsew")
        return canvas

    # --- Control Logic ---
    def toggle_loop(self):
        self.loop_is_running = not self.loop_is_running
        if self.loop_is_running:
            self.paused = False
            self.status_text = "Running"
            self.start_button.configure(text="Stop Loop")
            self.loop_thread = threading.Thread(target=self.main_loop, daemon=True)
            self.loop_thread.start()
        else:
            self.paused = True
            self.status_text = "Stopped"
            self.start_button.configure(text="Start Loop")
        self.status_label.configure(text=f"Status: {self.status_text}")

    def toggle_pause(self):
        if self.loop_is_running:
            self.paused = not self.paused
            self.status_text = "Paused" if self.paused else "Running"
            self.status_label.configure(text=f"Status: {self.status_text}")

    def toggle_history_recording(self):
        self.recording_history = not self.recording_history
        text = "Stop Recording" if self.recording_history else "Start Recording"
        self.history_button.configure(text=text)

    def clear_history(self):
        self.my_history.clear_history()
        self.history_text.delete('1.0', END)

    # --- UI Update Methods ---
    def update_telemetry_display(self):
        latest_log = self.my_telemetry.get_latest_log()
        if not latest_log: return
        self.telemetry_text.delete('1.0', END)
        for key, value in latest_log.items():
            if isinstance(value, (list, tuple, np.ndarray)):
                val_str = ", ".join(f"{v:.4f}" for v in value)
                self.telemetry_text.insert(END, f"{key.replace('_', ' ').title()}: [{val_str}]\n")
            else:
                self.telemetry_text.insert(END, f"{key.replace('_', ' ').title()}: {value}\n")

    def update_history_display(self):
        self.history_text.delete('1.0', END)
        for event in self.my_history.get_drift_history():
            ts = event['timestamp'].strftime('%H:%M:%S')
            err = event['error_magnitude']
            self.history_text.insert(END, f"[{ts}] Drift Detected! Error: {err:.4f}\n")

    def update_plots(self):
        """OPTIMIZED: Updates plot data without redrawing the entire figure."""
        # Update Correction Plot
        self.line_corr.set_data(range(len(self.correction_counts)), list(self.correction_counts))
        self.ax_corr.relim()
        self.ax_corr.autoscale_view()
        self.fig_corr.tight_layout() # Re-adjust layout dynamically
        self.canvas_corr.draw()

        # Update Drift Plot
        self.line_drift.set_data(range(len(self.drift_data)), list(self.drift_data))
        self.ax_drift.relim()
        self.ax_drift.autoscale_view()
        self.fig_drift.tight_layout() # Re-adjust layout dynamically
        self.canvas_drift.draw()

    # --- Main Simulation Loop ---
    def main_loop(self):
        """The core simulation loop running in a separate thread."""
        correction_count = 0
        tick_duration = 1.0 / config.SIMULATION_TICK_RATE_HZ

        while self.loop_is_running:
            start_time = time.monotonic()
            if self.paused:
                time.sleep(0.1)
                continue

            self.my_satellite.simulate_drift()
            current_location = self.my_sensor.get_current_position()
            target_location = config.INITIAL_TARGET_LOCATION

            distance_from_target = np.linalg.norm(np.array(target_location) - np.array(current_location))
            is_on_course = distance_from_target < config.ON_COURSE_THRESHOLD

            correction_vector = None
            if not is_on_course:
                correction_vector = self.my_controller.compute_correction(target_location, current_location)
                self.my_thruster.apply_thrust(self.my_satellite, correction_vector)
                correction_count += 1
                if self.recording_history:
                    self.my_history.record_drift(datetime.datetime.now(), current_location, distance_from_target, correction_vector)
                    self.after(0, self.update_history_display)

            # Log data
            self.drift_data.append(distance_from_target)
            self.correction_counts.append(correction_count)
            self.my_telemetry.log_status(datetime.datetime.now(), current_location, target_location, correction_vector, is_on_course)

            # Schedule GUI updates on the main thread
            self.after(0, self.update_telemetry_display)
            self.after(0, self.update_plots)

            # Ensure consistent loop timing
            elapsed_time = time.monotonic() - start_time
            sleep_time = max(0, tick_duration - elapsed_time)
            time.sleep(sleep_time)

    def on_closing(self):
        """Handles graceful application shutdown."""
        self.loop_is_running = False
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=1.0)
        self.login_root.destroy()  # Destroy the root window, which exits the mainloop
        sys.exit()

# --- Application Entry Point ---
if __name__ == "__main__":
    ctk.set_appearance_mode(config.APP_THEME_MODE)
    ctk.set_default_color_theme(config.APP_COLOR_THEME)

    # The login window is the one and only ROOT window for the entire app.
    login_window = LoginPage(on_login_success=None) # Callback is set after function definition

    def launch_main_app():
        """Hides the login window and creates the main application as a Toplevel window."""
        login_window.withdraw()
        main_app = SatelliteGUI(
            master=login_window,
            target_location=config.INITIAL_TARGET_LOCATION
        )
        main_app.grab_set() # Make the main app modal and focused

    # Now that the function is defined, assign it as the callback
    login_window.on_login_success = launch_main_app

    # This is the single mainloop call that runs the entire application
    login_window.mainloop()

