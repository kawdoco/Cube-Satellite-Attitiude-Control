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
from satellite_components import Satellite
from control_algorithm import PIDController
from telemetry import TelemetrySystem
from history import HistoryRecorder
from orbit_simulation import OrbitSimulationFrame
from login import LoginPage
from config import (
    SIMULATION_TICK_RATE_HZ,
    PID_GAINS,
    TELEMETRY_LOG_MAX_SIZE,
    HISTORY_LOG_MAX_SIZE,
    PLOT_DATA_MAX_POINTS,
    APP_THEME_MODE,
    APP_COLOR_THEME,
    DANGER_COLOR,
    DANGER_HOVER_COLOR,
    PLOT_BG_COLOR,
    CORRECTION_PLOT_COLOR,
    DRIFT_PLOT_COLOR,
    ON_COURSE_THRESHOLD,
    TARGET_ALTITUDE,
    TARGET_INCLINATION,
    TARGET_ECCENTRICITY,
    ICON_PATH
)

class MainApplication(ctk.CTk):
    """
    Main application window for the satellite control system GUI, adapted for orbital parameters.
    This is now the root window after the user logs in.
    """
    def __init__(self, target_altitude: float, target_inclination: float, target_eccentricity: float):
        super().__init__()

        # --- System Initialization ---
        # The Satellite now stores orbital parameters, not XYZ.
        self.my_satellite = Satellite(initial_altitude=target_altitude,
                                      initial_inclination=target_inclination,
                                      initial_eccentricity=target_eccentricity)
        
        # PID controller now targets orbital parameters.
        self.my_controller = PIDController(**PID_GAINS)
        
        self.my_telemetry = TelemetrySystem(max_log_size=TELEMETRY_LOG_MAX_SIZE)
        self.my_history = HistoryRecorder(max_history_size=HISTORY_LOG_MAX_SIZE)

        # Store target parameters for easy access
        self.target_altitude = target_altitude
        self.target_inclination = target_inclination
        self.target_eccentricity = target_eccentricity

        # --- Simulation State ---
        self.loop_is_running = False
        self.recording_history = False
        self.loop_thread = None
        self.paused = True
        self.status_text = "Paused"

        # --- OPTIMIZATION: Use deques for plot data to cap memory usage ---
        self.drift_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.correction_counts = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.tick_counter = 0
        
        # --- Set the application icon here, as it's the most reliable method. ---
        try:
            if ICON_PATH.exists():
                self.iconbitmap(ICON_PATH)
            else:
                print(f"Warning: Icon file not found at '{ICON_PATH}'. Skipping icon load.")
        except Exception as e:
            print(f"Error setting icon for main application: {e}")

        self._setup_gui()
        # The on_closing method now just handles the main app and thread.
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_gui(self) -> None:
        """Initializes the main GUI window and its components."""
        self.title("CubeSat Orbital Control")
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
        right_frame.grid_rowconfigure(0, weight=1)
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
                                                  fg_color=DANGER_COLOR, hover_color=DANGER_HOVER_COLOR)
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
        
        # Link the OrbitSimulationFrame to this controller.
        self.orbit_simulation_frame = OrbitSimulationFrame(orbit_tab, fg_color="transparent")
        self.orbit_simulation_frame.pack(fill="both", expand=True)

        # --- Live Plots ---
        plots_tab.grid_columnconfigure(0, weight=1)
        plots_tab.grid_rowconfigure((0, 1), weight=1)
        self.fig_corr, self.ax_corr = self._create_plot_figure("Correction Count Over Time")
        self.ax_corr.set_xlabel("Simulation Ticks", color='white')
        self.ax_corr.set_ylabel("Total Corrections", color='white')
        self.line_corr, = self.ax_corr.plot([], [], marker='o', color=CORRECTION_PLOT_COLOR)
        self.fig_corr.tight_layout()
        self.canvas_corr = self.embed_plot(self.fig_corr, plots_tab, 0)

        self.fig_drift, self.ax_drift = self._create_plot_figure("Orbital Parameter Error Over Time")
        self.ax_drift.set_xlabel("Simulation Ticks", color='white')
        self.ax_drift.set_ylabel("Error Magnitude", color='white')
        self.line_drift, = self.ax_drift.plot([], [], marker='o', color=DRIFT_PLOT_COLOR)
        self.fig_drift.tight_layout()
        self.canvas_drift = self.embed_plot(self.fig_drift, plots_tab, 1)

    def _create_plot_figure(self, title: str) -> tuple:
        """Helper to create a styled matplotlib Figure and Axes."""
        fig = plt.Figure(figsize=(8, 4), facecolor=PLOT_BG_COLOR)
        ax = fig.add_subplot(111, facecolor=PLOT_BG_COLOR)
        ax.set_title(title, color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
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
        self.telemetry_text.see(END)

    def update_history_display(self):
        self.history_text.delete('1.0', END)
        for event in self.my_history.get_drift_history():
            ts = event['timestamp'].strftime('%H:%M:%S')
            alt_change = event['altitude_change']
            self.history_text.insert(END, f"[{ts}] Altitude Drift: {alt_change:.4f}\n")
        self.history_text.see(END)

    def update_plots(self):
        """OPTIMIZED: Updates plot data without redrawing the entire figure."""
        # Update Correction Plot
        self.line_corr.set_data(range(len(self.correction_counts)), list(self.correction_counts))
        self.ax_corr.relim()
        self.ax_corr.autoscale_view()
        self.fig_corr.tight_layout()
        self.canvas_corr.draw()

        # Update Drift Plot
        self.line_drift.set_data(range(len(self.drift_data)), list(self.drift_data))
        self.ax_drift.relim()
        self.ax_drift.autoscale_view()
        self.fig_drift.tight_layout()
        self.canvas_drift.draw()

    # --- Main Simulation Loop ---
    def main_loop(self):
        """The core simulation loop running in a separate thread."""
        correction_count = 0
        tick_duration = 1.0 / SIMULATION_TICK_RATE_HZ

        while self.loop_is_running:
            start_time = time.monotonic()
            if self.paused:
                time.sleep(0.1)
                continue
            
            # Record the altitude before drift
            initial_altitude = self.my_satellite.get_altitude()
            
            # Simulate orbital drift based on a simple model
            self.my_satellite.simulate_orbital_drift()
            
            # Get current orbital parameters
            current_params = self.my_satellite.get_orbital_parameters()
            
            # Define target parameters as a tuple
            target_params = (self.target_altitude, self.target_inclination, self.target_eccentricity)
            
            # Calculate error vector and magnitude
            error_vector = np.array(target_params) - np.array(current_params)
            error_magnitude = np.linalg.norm(error_vector)
            is_on_course = error_magnitude < ON_COURSE_THRESHOLD

            correction_vector = None
            altitude_change = 0
            if not is_on_course:
                # PID controller corrects based on the error vector of the parameters
                correction_vector = self.my_controller.compute_correction(target_params, current_params)
                
                # Apply the correction to the satellite's orbital parameters
                self.my_satellite.apply_orbital_correction(correction_vector)
                
                correction_count += 1
                
                # Calculate the change in altitude for history logging
                altitude_change = self.my_satellite.get_altitude() - initial_altitude

                if self.recording_history:
                    # Log drift event with new parameters
                    self.my_history.record_drift(datetime.datetime.now(), altitude_change)
                    self.after(0, self.update_history_display)
            
            # Log telemetry data
            self.drift_data.append(error_magnitude)
            self.correction_counts.append(correction_count)
            self.my_telemetry.log_status(
                datetime.datetime.now(), 
                current_orbital_params=current_params,
                target_orbital_params=target_params,
                correction_vector=correction_vector,
                is_on_course=is_on_course
            )

            # Update the OrbitSimulationFrame's state
            self.after(0, lambda: self.orbit_simulation_frame.set_orbital_parameters(
                self.my_satellite.get_altitude(),
                self.my_satellite.get_inclination(),
                self.my_satellite.get_eccentricity()
            ))
            
            # Schedule GUI updates on the main thread
            self.after(0, self.update_telemetry_display)
            self.after(0, self.update_plots)
            self.tick_counter += 1

            # Ensure consistent loop timing
            elapsed_time = time.monotonic() - start_time
            sleep_time = max(0, tick_duration - elapsed_time)
            time.sleep(sleep_time)

    def on_closing(self):
        """Handles graceful application shutdown."""
        self.loop_is_running = False
        if self.loop_thread and self.loop_thread.is_alive():
            self.loop_thread.join(timeout=1.0)
        self.destroy()
        sys.exit()

# --- Application Entry Point ---
if __name__ == "__main__":
    ctk.set_appearance_mode(APP_THEME_MODE)
    ctk.set_default_color_theme(APP_COLOR_THEME)
    
    # The login window is the one and only ROOT window for the entire app.
    login_window = LoginPage(on_login_success=None)
    
    # Set the icon for the login window
    try:
        if ICON_PATH.exists():
            login_window.iconbitmap(ICON_PATH)
        else:
            print(f"Warning: Icon file not found at '{ICON_PATH}'. Skipping icon load.")
    except Exception as e:
        print(f"Error setting icon for login window: {e}")

    def launch_main_app():
        """Hides the login window and creates the main application."""
        # Destroy the login window, then create the main app as the new root.
        login_window.destroy()
        main_app = MainApplication(
            target_altitude=TARGET_ALTITUDE,
            target_inclination=TARGET_INCLINATION,
            target_eccentricity=TARGET_ECCENTRICITY
        )
        main_app.mainloop()

    login_window.on_login_success = launch_main_app
    login_window.mainloop()
