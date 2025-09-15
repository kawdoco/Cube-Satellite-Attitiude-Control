"""
login.py

Handles the user authentication window for the application.
Optimized to use relative paths for assets, making it portable.
"""
import customtkinter as ctk
from PIL import Image
from tkinter import messagebox
from config import ASSETS_PATH  # Use centralized config for paths

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
            image_path = ASSETS_PATH / "login.png"
            self.original_bg_image = Image.open(image_path)
        except FileNotFoundError:
            print(f"Warning: Login background image not found at '{image_path}'. Using a fallback color.")
            self.configure(fg_color="#1a1a1a")

        # --- Background Label ---
        self.bg_label = ctk.CTkLabel(self, text="")
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Bind the resize event to handle the background image scaling
        self.bind("<Configure>", self._resize_image)

        # --- Login Frame ---
        login_frame = ctk.CTkFrame(self, corner_radius=10, fg_color="#1a1a1a")
        login_frame.place(relx=0.25, rely=0.5, anchor=ctk.CENTER)

        ctk.CTkLabel(login_frame, text="Mission Control Login", font=("Roboto", 24, "bold")).pack(pady=(30, 20))

        # --- Username ---
        self.username_entry = ctk.CTkEntry(login_frame, width=220, placeholder_text="Username")
        self.username_entry.pack(pady=12, padx=30)

        # --- Password ---
        self.password_entry = ctk.CTkEntry(login_frame, width=220, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=12, padx=30)

        # --- Login Button ---
        login_button = ctk.CTkButton(login_frame, text="Login", command=self.attempt_login, width=220)
        login_button.pack(pady=(20, 30))

        # Initial call to set the background
        self._resize_image(None)

    def _resize_image(self, event) -> None:
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
        """Validates credentials and proceeds if correct."""
        if self.username_entry.get() == "admin" and self.password_entry.get() == "123":
            self.on_login_success()
        else:
            messagebox.showerror("Login Failed", "Invalid username or password.")
