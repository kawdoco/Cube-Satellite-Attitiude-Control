import sys
import time
import datetime
import threading
from tkinter import END, scrolledtext, messagebox
from collections import deque
import customtkinter as ctk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

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
    PLOT_DATA_MAX_POINTS, # Re-enabled for scrolling plots
    APP_THEME_MODE,
    APP_COLOR_THEME,
    DANGER_COLOR,
    DANGER_HOVER_COLOR,
    PLOT_BG_COLOR,
    ON_COURSE_THRESHOLD,
    TARGET_ALTITUDE,
    TARGET_INCLINATION,
    TARGET_ECCENTRICITY,
    ICON_PATH,
    PLANET_DATA  # Import new planet data
)

class MainApplication(ctk.CTk):
    """
    Main application window for the satellite control system GUI.
    The layout is structured to match the provided dashboard image.
    """
    def __init__(self):
        super().__init__()

        # --- System Initialization ---
        self.target_altitude = TARGET_ALTITUDE
        self.target_inclination = TARGET_INCLINATION
        self.target_eccentricity = TARGET_ECCENTRICITY
        self.my_satellite = Satellite(initial_altitude=self.target_altitude,
                                      initial_inclination=self.target_inclination,
                                      initial_eccentricity=self.target_eccentricity)
        self.my_controller = PIDController(**PID_GAINS)
        self.my_telemetry = TelemetrySystem(max_log_size=TELEMETRY_LOG_MAX_SIZE)
        self.my_history = HistoryRecorder(max_history_size=HISTORY_LOG_MAX_SIZE)

        # --- Simulation State ---
        self.loop_is_running = False
        self.recording_history = False
        self.loop_thread = None
        self.paused = True
        self.status_text = "Paused"
        self.correction_count = 0 # <-- NEW: Correction counter

        # --- Plot Data (deques now have maxlen for scrolling) ---
        self.x_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.y_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.z_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        
        # --- New Plot Data for Corrections (with maxlen) ---
        self.corr_alt_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.corr_inc_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        self.corr_ecc_data = deque(maxlen=PLOT_DATA_MAX_POINTS)
        
        try:
            if ICON_PATH.exists():
                self.iconbitmap(ICON_PATH)
        except Exception as e:
            print(f"Error setting icon: {e}")

        self._setup_gui()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_gui(self) -> None:
        """Initializes the main GUI dashboard layout."""
        self.title("CubeSat Mission Control Dashboard")
        self.geometry("1800x1000")
        self.minsize(1400, 800)

        # --- Main Grid Configuration (2 columns) ---
        self.grid_columnconfigure(0, weight=3)  # Left panel is wider
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Left Panel ---
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_panel.grid_rowconfigure(0, weight=0) # Top buttons
        self.left_panel.grid_rowconfigure(1, weight=0) # Status label
        self.left_panel.grid_rowconfigure(2, weight=1) # Orbit sim takes most space
        self.left_panel.grid_rowconfigure(3, weight=0) # Controls are fixed height
        self.left_panel.grid_columnconfigure(0, weight=1)

        # --- Right Panel ---
        self.right_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.right_panel.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.right_panel.grid_rowconfigure(0, weight=5) # Plot takes more space
        self.right_panel.grid_rowconfigure(1, weight=3) # Telemetry
        self.right_panel.grid_rowconfigure(2, weight=3) # History
        self.right_panel.grid_columnconfigure(0, weight=1)

        # --- Populate Panels ---
        self._setup_left_panel()
        self._setup_right_panel()

    def _setup_left_panel(self):
        """Sets up the orbit simulation and control sliders on the left panel."""
        # --- Top Button Bar ---
        self._setup_top_buttons(self.left_panel)
        
        # --- Status Label ---
        self.status_label = ctk.CTkLabel(self.left_panel, text=f"Status: {self.status_text}", font=("Roboto", 16))
        self.status_label.grid(row=1, column=0, padx=10, pady=(5, 0), sticky="nw")
        
        # --- Orbit Simulation Frame ---
        self.orbit_sim_frame = OrbitSimulationFrame(self.left_panel)
        self.orbit_sim_frame.grid(row=2, column=0, sticky="nsew", pady=(0, 10))

        # --- Correction Message Label (Overlaid on sim frame) ---
        self.correction_message_label = ctk.CTkLabel(self.orbit_sim_frame, text="", font=("Roboto", 18, "bold"), 
                                                     text_color="white", fg_color="#0D9F00", corner_radius=5)
        # This label is hidden until .place() is called by _show_correction_message

        # --- Bottom Controls Container ---
        bottom_controls_frame = ctk.CTkFrame(self.left_panel)
        bottom_controls_frame.grid(row=3, column=0, sticky="ew")
        bottom_controls_frame.grid_columnconfigure(0, weight=1) # Only one column for sliders

        # --- Parameter Controls (Sliders) ---
        param_frame = ctk.CTkFrame(bottom_controls_frame, fg_color="transparent")
        param_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self._setup_parameter_controls(param_frame)
    
    def _setup_top_buttons(self, parent: ctk.CTkFrame):
        """Creates the horizontal button bar at the top of the left panel."""
        top_button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_button_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        top_button_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.start_button = ctk.CTkButton(top_button_frame, text="Start/Pause", command=self.toggle_loop)
        self.start_button.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.stop_button = ctk.CTkButton(top_button_frame, text="Stop", command=self.stop_loop,
                                         fg_color=DANGER_COLOR, hover_color=DANGER_HOVER_COLOR)
        self.stop_button.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.correct_button = ctk.CTkButton(top_button_frame, text="Correct Orbit", command=self.correct_orbit_to_default)
        self.correct_button.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.history_button = ctk.CTkButton(top_button_frame, text="Start History", command=self.toggle_history_recording)
        self.history_button.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.clear_history_button = ctk.CTkButton(top_button_frame, text="Clear History", command=self.clear_history)
        self.clear_history_button.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

    def _setup_parameter_controls(self, parent: ctk.CTkFrame):
        """Sets up the altitude, inclination, eccentricity, and orbit speed controls."""
        parent.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1) # 6 columns
        parent.grid_rowconfigure(0, weight=0) # Labels
        parent.grid_rowconfigure(1, weight=1) # Sliders
        parent.grid_rowconfigure(2, weight=0) # Planet selector
        parent.grid_rowconfigure(3, weight=0) # Background selector
        
        # --- Altitude ---
        self.alt_label = ctk.CTkLabel(parent, text=f"Altitude: {TARGET_ALTITUDE:.0f} km")
        self.alt_label.grid(row=0, column=0, padx=10, pady=(10, 0))
        self.alt_slider = ctk.CTkSlider(parent, from_=500, to=40000, command=lambda v: self.alt_label.configure(text=f"Altitude: {v:.0f} km"))
        self.alt_slider.set(TARGET_ALTITUDE)
        self.alt_slider.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        # --- Inclination ---
        self.inc_label = ctk.CTkLabel(parent, text=f"Inclination: {TARGET_INCLINATION:.1f}°")
        self.inc_label.grid(row=0, column=1, padx=10, pady=(10, 0))
        self.inc_slider = ctk.CTkSlider(parent, from_=0, to=180, command=lambda v: self.inc_label.configure(text=f"Inclination: {v:.1f}°"))
        self.inc_slider.set(TARGET_INCLINATION)
        self.inc_slider.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="ew")

        # --- Eccentricity ---
        self.ecc_label = ctk.CTkLabel(parent, text=f"Eccentricity: {TARGET_ECCENTRICITY:.3f}")
        self.ecc_label.grid(row=0, column=2, padx=10, pady=(10, 0))
        self.ecc_slider = ctk.CTkSlider(parent, from_=0, to=0.999, command=lambda v: self.ecc_label.configure(text=f"Eccentricity: {v:.3f}"))
        self.ecc_slider.set(TARGET_ECCENTRICITY)
        self.ecc_slider.grid(row=1, column=2, padx=10, pady=(0, 10), sticky="ew")
        
        # --- Orbit Speed ---
        self.speed_label = ctk.CTkLabel(parent, text="Orbit Speed: 1.0x")
        self.speed_label.grid(row=0, column=3, padx=10, pady=(10, 0))
        self.speed_slider = ctk.CTkSlider(parent, from_=0.1, to=20.0, command=self._on_speed_change) # Increased range
        self.speed_slider.set(1.0)
        self.speed_slider.grid(row=1, column=3, padx=10, pady=(0, 10), sticky="ew")

        # --- Planet Selector (Tab-style) ---
        ctk.CTkLabel(parent, text="Target Planet:").grid(row=2, column=0, padx=10, pady=(5, 10), sticky="e")
        self.planet_selector = ctk.CTkSegmentedButton(parent, values=list(PLANET_DATA.keys()),
                                                      command=self._on_planet_change)
        self.planet_selector.set("Earth")
        self.planet_selector.grid(row=2, column=1, columnspan=4, padx=10, pady=(5, 10), sticky="ew")
        
        # --- NEW: Background Symbol Buttons ---
        ctk.CTkLabel(parent, text="Background:").grid(row=3, column=0, padx=10, pady=(5, 10), sticky="e")
        
        # Create a frame to hold the buttons
        bg_button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        bg_button_frame.grid(row=3, column=1, columnspan=4, padx=10, pady=(5, 10), sticky="ew")
        bg_button_frame.grid_columnconfigure((0, 1, 2), weight=1) # Make buttons expand
        
        self.bg_btn_black = ctk.CTkButton(bg_button_frame, text="🌙", font=("Segoe UI Emoji", 18),
                                          command=lambda: self._on_background_change("Black"))
        self.bg_btn_black.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.bg_btn_blue = ctk.CTkButton(bg_button_frame, text="✨", font=("Segoe UI Emoji", 18),
                                         command=lambda: self._on_background_change("Dark Blue"))
        self.bg_btn_blue.grid(row=0, column=1, padx=5, sticky="ew")

        self.bg_btn_streak = ctk.CTkButton(bg_button_frame, text="☄️", font=("Segoe UI Emoji", 18),
                                           command=lambda: self._on_background_change("Starfield"))
        self.bg_btn_streak.grid(row=0, column=2, padx=5, sticky="ew")
        # --- END NEW ---
        
        # --- Apply Button ---
        self.apply_button = ctk.CTkButton(parent, text="Apply Target", command=self._on_apply_target)
        self.apply_button.grid(row=0, column=5, rowspan=4, padx=10, pady=10, sticky="ns") # Spans 4 rows now

    def _setup_right_panel(self):
        """Sets up the 3D plot and telemetry/history logs on the right panel."""
        
        # --- Create Tab View for Plots ---
        plot_tab_view = ctk.CTkTabview(self.right_panel)
        plot_tab_view.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        plot_tab_view.add("Position")
        plot_tab_view.add("Correction")
        
        # --- 3D Position Plot Tab ---
        pos_tab = plot_tab_view.tab("Position")
        pos_tab.grid_rowconfigure(0, weight=1)
        pos_tab.grid_columnconfigure(0, weight=1)
        
        self.fig_pos, self.ax_pos = self._create_plot_figure(
            y_label="Position (km)",
            line_labels=['X Position (km)', 'Y Position (km)', 'Z Position (km)'],
            colors=['r', 'b', 'g']
        )
        self.canvas_pos = FigureCanvasTkAgg(self.fig_pos, master=pos_tab)
        self.canvas_pos.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        toolbar_pos = NavigationToolbar2Tk(self.canvas_pos, pos_tab, pack_toolbar=False)
        toolbar_pos.update()
        toolbar_pos.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # Store lines for position
        self.line_x = self.ax_pos.lines[0]
        self.line_y = self.ax_pos.lines[1]
        self.line_z = self.ax_pos.lines[2]

        # --- Correction Plot Tab ---
        corr_tab = plot_tab_view.tab("Correction")
        corr_tab.grid_rowconfigure(0, weight=1)
        corr_tab.grid_columnconfigure(0, weight=1)
        corr_tab.grid_rowconfigure(1, weight=0) # <-- NEW: For toolbar
        corr_tab.grid_rowconfigure(2, weight=0) # <-- NEW: For counter
        
        self.fig_corr, self.ax_corr = self._create_plot_figure(
            y_label="Correction Magnitude",
            line_labels=['Altitude Correction', 'Inclination Correction', 'Eccentricity Correction'],
            colors=['#FFA500', '#00FFFF', '#FF00FF'] # Orange, Cyan, Magenta
        )
        self.canvas_corr = FigureCanvasTkAgg(self.fig_corr, master=corr_tab)
        self.canvas_corr.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        
        toolbar_corr = NavigationToolbar2Tk(self.canvas_corr, corr_tab, pack_toolbar=False)
        toolbar_corr.update()
        toolbar_corr.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # --- NEW: Correction Counter Label ---
        self.correction_counter_label = ctk.CTkLabel(corr_tab, text="Total Corrections Applied: 0", font=("Roboto", 14))
        self.correction_counter_label.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 5))
        # --- END NEW ---
        
        # Store lines for correction
        self.line_corr_alt = self.ax_corr.lines[0]
        self.line_corr_inc = self.ax_corr.lines[1]
        self.line_corr_ecc = self.ax_corr.lines[2]
        
        # --- Telemetry Log ---
        telemetry_container = ctk.CTkFrame(self.right_panel)
        telemetry_container.grid(row=1, column=0, sticky="nsew", pady=(0, 10))
        telemetry_container.grid_rowconfigure(1, weight=1)
        telemetry_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(telemetry_container, text="Real-time Telemetry Data (Altitude/Error/Correction)", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=5)
        self.telemetry_text = scrolledtext.ScrolledText(telemetry_container, wrap='word', height=10, bg="#2b2b2b", fg="white", bd=0)
        self.telemetry_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # --- History Log ---
        history_container = ctk.CTkFrame(self.right_panel)
        history_container.grid(row=2, column=0, sticky="nsew")
        history_container.grid_rowconfigure(1, weight=1)
        history_container.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(history_container, text="Drifting History Log", font=("Roboto", 16, "bold")).grid(row=0, column=0, pady=5)
        self.history_text = scrolledtext.ScrolledText(history_container, wrap='word', height=10, bg="#2b2b2b", fg="white", bd=0)
        self.history_text.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def _create_plot_figure(self, y_label: str, line_labels: list, colors: list) -> tuple:
        """Helper to create a styled matplotlib Figure and Axes for any plot."""
        fig = plt.Figure(figsize=(8, 4), facecolor=PLOT_BG_COLOR)
        ax = fig.add_subplot(111, facecolor=PLOT_BG_COLOR)
        ax.set_xlabel("Time Step", color='white')
        ax.set_ylabel(y_label, color='white')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['top'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['right'].set_color('white')
        
        # --- ADDED GRID ---
        ax.grid(True, linestyle='--', alpha=0.6, color='gray')

        # Define lines for the plot
        for label, color in zip(line_labels, colors):
            ax.plot([], [], color=color, linestyle='-', label=label)
        
        ax.legend(labelcolor='white')
        fig.tight_layout()
        return fig, ax

    # --- Control Logic & Callbacks ---
    def _on_apply_target(self):
        """
        Callback to update the simulation's target parameters from the GUI sliders.
        This function now instantly applies the new parameters to the satellite
        and resets the PID controller to maintain the new orbit.
        """
        # 1. Get new target values from sliders
        new_target_altitude = self.alt_slider.get()
        new_target_inclination = self.inc_slider.get()
        new_target_eccentricity = self.ecc_slider.get()

        # 2. Update the internal target variables for the PID
        self.target_altitude = new_target_altitude
        self.target_inclination = new_target_inclination
        self.target_eccentricity = new_target_eccentricity
        
        # 3. (THE FIX) Instantly apply these new parameters to the satellite itself.
        current_alt, current_inc, current_ecc = self.my_satellite.get_orbital_parameters()
        
        correction_vector = [
            new_target_altitude - current_alt,
            new_target_inclination - current_inc,
            new_target_eccentricity - current_ecc
        ]
        self.my_satellite.apply_orbital_correction(correction_vector)
        
        # 4. (THE FIX) Force the simulation to update its visual path immediately
        #    This ensures the GUI reflects the change instantly.
        self.orbit_sim_frame.set_orbital_parameters(
            new_target_altitude, 
            new_target_inclination, 
            new_target_eccentricity
        )
        
        # 5. (THE FIX) Reset the PID controller
        #    This is crucial. The satellite is now *at* the new target,
        #    so the PID's integral and derivative terms must be cleared.
        self._reset_pid()
        
        # --- (USER REQUEST) ---
        # self.correction_count = 0 # <-- REMOVED AS REQUESTED
        # self.update_correction_counter() # <-- REMOVED AS REQUESTED
        # --- END (USER REQUEST) ---

        print(f"INFO: New target parameters applied and orbit instantly corrected: Alt={self.target_altitude:.2f}, Inc={self.target_inclination:.2f}, Ecc={self.target_eccentricity:.2f}")
        
        # 6. Show a confirmation message
        self._show_correction_message("New Target Orbit Applied")

    def _on_speed_change(self, value):
        """Updates the animation speed of the orbit simulation."""
        speed = float(value)
        self.speed_label.configure(text=f"Orbit Speed: {speed:.1f}x")
        self.orbit_sim_frame.update_speed(speed)

    def _on_planet_change(self, planet_name: str):
        """Tells the orbit simulation to switch planets."""
        if self.orbit_sim_frame:
            self.orbit_sim_frame.set_planet(planet_name)
            # When planet changes, we must re-compute the orbit
            # based on the new planet's radius
            self.orbit_sim_frame.set_orbital_parameters(
                self.my_satellite.get_altitude(),
                self.my_satellite.get_inclination(),
                self.my_satellite.get_eccentricity()
            )

    # --- NEW: Background Change Callback ---
    def _on_background_change(self, bg_name: str):
        """Tells the orbit simulation to change its background color."""
        if self.orbit_sim_frame:
            self.orbit_sim_frame.set_background(bg_name)
    # --- END NEW ---

    def _reset_pid(self):
        """Resets the PID controller's internal state."""
        self.my_controller.reset()
        print("INFO: PID Controller has been reset.")

    def correct_orbit_to_default(self):
        """Resets the satellite to the program's default orbital parameters."""
        # Apply the default parameters from config to the satellite
        self.my_satellite.apply_orbital_correction([
            TARGET_ALTITUDE - self.my_satellite.get_altitude(),
            TARGET_INCLINATION - self.my_satellite.get_inclination(),
            TARGET_ECCENTRICITY - self.my_satellite.get_eccentricity()
        ])
        
        # Reset the UI sliders and labels to match the default values
        self.alt_slider.set(TARGET_ALTITUDE)
        self.inc_slider.set(TARGET_INCLINATION)
        self.ecc_slider.set(TARGET_ECCENTRICITY)
        self.alt_label.configure(text=f"Altitude: {TARGET_ALTITUDE:.0f} km")
        self.inc_label.configure(text=f"Inclination: {TARGET_INCLINATION:.1f}°")
        self.ecc_label.configure(text=f"Eccentricity: {TARGET_ECCENTRICITY:.3f}")

        # Also reset the internal target variables to default
        self.target_altitude = TARGET_ALTITUDE
        self.target_inclination = TARGET_INCLINATION
        self.target_eccentricity = TARGET_ECCENTRICITY
        
        # Force immediate visual update of the orbit path
        self.orbit_sim_frame.set_orbital_parameters(*self.my_satellite.get_orbital_parameters())
        
        # Reset the PID controller
        self._reset_pid()
        
        # --- NEW: Reset correction counter ---
        self.correction_count = 0
        self.update_correction_counter()
        # --- END NEW ---
        
        print("INFO: 'Correct Orbit' applied. Orbit reset to default starting position.")
        # Show the confirmation message
        self._show_correction_message("Orbit Correction Message")
        
    def _show_correction_message(self, message: str):
        """Displays a temporary message overlayed on the orbit simulation."""
        self.correction_message_label.configure(text=message)
        self.correction_message_label.place(relx=0.5, rely=0.5, anchor="center")
        # Hide the label after 3000 milliseconds (3 seconds)
        self.correction_message_label.after(3000, self.correction_message_label.place_forget)

    def clear_history(self):
        """Clears the drift history log."""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to clear the drift history log?"):
            self.my_history.clear_history()
            self.update_history_display()
            
            # --- NEW: Reset correction counter ---
            self.correction_count = 0
            self.update_correction_counter()
            # --- END NEW ---
            
            print("INFO: Drift history cleared.")

    def toggle_loop(self):
        if not self.loop_is_running:
            self.loop_is_running = True
            self.paused = False
            self.status_text = "Running"
            # --- FIX 2: Start the animation ---
            self.orbit_sim_frame.set_animation_state(True) 
            self.loop_thread = threading.Thread(target=self.main_loop, daemon=True)
            self.loop_thread.start()
        else:
            self.paused = not self.paused
            self.status_text = "Paused" if self.paused else "Running"
            # --- FIX 2: Pause or resume the animation ---
            self.orbit_sim_frame.set_animation_state(not self.paused) 
        self.status_label.configure(text=f"Status: {self.status_text}")
        
    def stop_loop(self):
        """Stops the main simulation loop completely."""
        if self.loop_is_running:
            self.loop_is_running = False
            if self.loop_thread and self.loop_thread.is_alive():
                self.loop_thread.join(timeout=1.0) # Wait for thread to stop
            self.loop_thread = None
            self.paused = True
            self.status_text = "Stopped"
            # --- FIX 2: Stop the animation ---
            self.orbit_sim_frame.set_animation_state(False)
            self.status_label.configure(text=f"Status: {self.status_text}")
            print("INFO: Simulation stopped.")
        
    def toggle_history_recording(self):
        self.recording_history = not self.recording_history
        text = "Stop History" if self.recording_history else "Start History"
        self.history_button.configure(text=text)

    # --- UI Update Methods (called from main_loop) ---
    def update_telemetry_display(self):
        latest_log = self.my_telemetry.get_latest_log()
        if not latest_log: return
        self.telemetry_text.delete('1.0', END)
        for key, value in latest_log.items():
            if isinstance(value, (list, tuple, np.ndarray)):
                val_str = ", ".join(f"{v:.4f}" for v in value if v is not None)
                self.telemetry_text.insert(END, f"{key.replace('_', ' ').title()}: [{val_str}]\n")
            elif isinstance(value, float):
                 self.telemetry_text.insert(END, f"{key.replace('_', ' ').title()}: {value:.4f}\n")
            else:
                self.telemetry_text.insert(END, f"{key.replace('_', ' ').title()}: {value}\n")
        self.telemetry_text.see(END)

    def update_history_display(self):
        self.history_text.delete('1.0', END)
        for event in self.my_history.get_drift_history():
            ts = event['timestamp'].strftime('%H:%M:%S')
            alt_change = event['altitude_change']
            self.history_text.insert(END, f"[{ts}] Altitude Drift: {alt_change:+.4f} km\n")
        self.history_text.see(END)

    def update_plots(self):
        """Updates plot data without redrawing the entire figure."""
        # --- Update Position Plot ---
        pos_ticks = range(len(self.x_data))
        self.line_x.set_data(pos_ticks, list(self.x_data))
        self.line_y.set_data(pos_ticks, list(self.y_data))
        self.line_z.set_data(pos_ticks, list(self.z_data))

        self.ax_pos.relim()
        self.ax_pos.autoscale_view()
        self.fig_pos.tight_layout()
        self.canvas_pos.draw()

        # --- Update Correction Plot ---
        corr_ticks = range(len(self.corr_alt_data))
        self.line_corr_alt.set_data(corr_ticks, list(self.corr_alt_data))
        self.line_corr_inc.set_data(corr_ticks, list(self.corr_inc_data))
        self.line_corr_ecc.set_data(corr_ticks, list(self.corr_ecc_data))

        self.ax_corr.relim()
        self.ax_corr.autoscale_view()
        self.fig_corr.tight_layout()
        self.canvas_corr.draw()
        
    # --- NEW: Update counter label ---
    def update_correction_counter(self):
        """Updates the correction counter label on the GUI."""
        if hasattr(self, 'correction_counter_label'):
            self.correction_counter_label.configure(text=f"Total Corrections Applied: {self.correction_count}")
    # --- END NEW ---

    def update_simulation_and_data(self):
        """
        Updates the orbit simulation visuals and logs the new position data for the plot.
        
        --- (THE FIX) ---
        Removed the call to self.orbit_sim_frame.set_orbital_parameters().
        This function should ONLY log data for the 3D plot.
        The orbit path itself should only be updated by manual user actions 
        (like _on_apply_target or correct_orbit_to_default).
        """
        # self.orbit_sim_frame.set_orbital_parameters(*self.my_satellite.get_orbital_parameters()) # <-- THIS LINE WAS THE BUG
        
        current_pos_3d = self.orbit_sim_frame.get_current_position()
        
        # Log the position data in kilometers directly
        self.x_data.append(current_pos_3d[0])
        self.y_data.append(current_pos_3d[1])
        self.z_data.append(current_pos_3d[2])

    # --- Main Simulation Loop ---
    def main_loop(self):
        """The core simulation loop running in a separate thread."""
        tick_duration = 1.0 / SIMULATION_TICK_RATE_HZ

        while self.loop_is_running:
            start_time = time.monotonic()
            if self.paused:
                time.sleep(0.1)
                continue
            
            # --- Simulation Step ---
            initial_altitude = self.my_satellite.get_altitude()
            self.my_satellite.simulate_orbital_drift()
            
            # --- PID Control Step ---
            current_params = self.my_satellite.get_orbital_parameters()
            target_params = (self.target_altitude, self.target_inclination, self.target_eccentricity)
            error_magnitude = np.linalg.norm(np.array(target_params) - np.array(current_params))
            is_on_course = error_magnitude < ON_COURSE_THRESHOLD

            correction_vector = None
            if not is_on_course:
                correction_vector = self.my_controller.compute_correction(target_params, current_params)
                self.my_satellite.apply_orbital_correction(correction_vector)
                self.correction_count += 1 # <-- NEW: Increment counter
            
            # --- Logging and History ---
            if self.recording_history:
                altitude_change = self.my_satellite.get_altitude() - initial_altitude
                self.my_history.record_drift(datetime.datetime.now(), altitude_change)
                self.after(0, self.update_history_display)
            
            self.my_telemetry.log_status(
                datetime.datetime.now(), 
                current_orbital_params=current_params,
                target_orbital_params=target_params,
                correction_vector=correction_vector,
                is_on_course=is_on_course
            )
            
            # --- Log data for Correction Plot ---
            if correction_vector:
                self.corr_alt_data.append(correction_vector[0])
                self.corr_inc_data.append(correction_vector[1])
                self.corr_ecc_data.append(correction_vector[2])
            else:
                self.corr_alt_data.append(0.0)
                self.corr_inc_data.append(0.0)
                self.corr_ecc_data.append(0.0)

            # --- Schedule GUI updates on the main thread ---
            self.after(0, self.update_simulation_and_data)
            self.after(0, self.update_telemetry_display)
            self.after(0, self.update_plots)
            self.after(0, self.update_correction_counter) # <-- NEW: Update counter label

            # --- Tick Rate Control ---
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
    
    def launch_main_app():
        login_window.destroy()
        main_app = MainApplication()
        main_app.mainloop()

    login_window = LoginPage(on_login_success=launch_main_app)
    
    try:
        if ICON_PATH.exists():
            login_window.iconbitmap(ICON_PATH)
    except Exception as e:
        print(f"Error setting icon for login window: {e}")

    login_window.mainloop()