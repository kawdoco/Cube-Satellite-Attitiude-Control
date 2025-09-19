"""
login.py

Handles the user authentication window for the application.
Optimized to use relative paths for assets, making it portable.
"""
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from config import ASSETS_PATH, LOGIN_BG_IMAGE_FILENAME # Use centralized config for paths

class LoginPage(ctk.CTk):
    """
    Creates the login window.
    It authenticates the user and calls a callback function on success.
    """
    def __init__(self, on_login_success: callable):
        super().__init__()
        self.on_login_success = on_login_success
        self.title("CubeSat Login")
        self.geometry("1000x600")
        self.minsize(600, 400)

        # --- Load and store the original image using a relative path ---
        self.original_bg_image = None
        try:
            image_path = ASSETS_PATH / LOGIN_BG_IMAGE_FILENAME
            self.original_bg_image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Warning: Login background image not found at '{image_path}'. Using a fallback color.")
            self.configure(fg_color="#1a1a1a")

        # --- Background Label ---
        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # --- Login Frame ---
        self.login_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.login_frame.place(relx=0.2, rely=0.5, anchor="center")
        self.login_frame.grid_columnconfigure(0, weight=1)
        
        self.title_label = ctk.CTkLabel(self.login_frame, text="CubeSat Login", font=("Roboto", 24, "bold"))
        self.title_label.grid(row=0, column=0, pady=(20, 10))
        
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Username", width=250)
        self.username_entry.grid(row=1, column=0, padx=20, pady=10)
        
        self.password_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Password", show="*", width=250)
        self.password_entry.grid(row=2, column=0, padx=20, pady=10)
        
        self.login_button = ctk.CTkButton(self.login_frame, text="Login", width=250, command=self.attempt_login)
        self.login_button.grid(row=3, column=0, padx=20, pady=20)

        self.bind("<Configure>", self.on_window_resize)

    def on_window_resize(self, event) -> None:
        """Dynamically resizes the background image to fit the window without distortion."""
        if not self.original_bg_image:
            return  # No image to resize

        new_width = self.winfo_width()
        new_height = self.winfo_height()

        if new_width <= 1 or new_height <= 1:
            return # Avoid division by zero on minimize

        # --- Resizing logic ---
        img_width, img_height = self.original_bg_image.size
        aspect_ratio_window = new_width / new_height
        aspect_ratio_img = img_width / img_height

        if aspect_ratio_img > aspect_ratio_window:
            resize_height = new_height
            resize_width = int(resize_height * aspect_ratio_img)
        else:
            resize_width = new_width
            resize_height = int(resize_width / aspect_ratio_img)

        bg_image_resized = self.original_bg_image.resize((resize_width, resize_height), Image.LANCZOS)
        bg_image = ctk.CTkImage(light_image=bg_image_resized, size=(new_width, new_height))

        self.bg_label.configure(image=bg_image)
        self.bg_label.image = bg_image  # Keep a reference

    def attempt_login(self) -> None:
        """Validates credentials and proceeds if successful."""
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username == "admin" and password == "password":  # Hardcoded credentials for example
            messagebox.showinfo("Login Success", "Welcome, Admin!")
            if self.on_login_success:
                self.on_login_success()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
