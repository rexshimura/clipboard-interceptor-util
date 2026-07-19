import os
import sys
import time
import threading
from datetime import datetime
from PIL import Image, ImageDraw, ImageGrab, ImageChops
import customtkinter as ctk
import pystray
from pystray import MenuItem as item
from tkinter import filedialog

# Global Application States
app_active = True
tray_icon = None
status_widget_instance = None
main_root = None  # Hidden master anchor for thread safety

# Default folder settings
DEFAULT_DOWNLOADS = os.path.join(os.environ['USERPROFILE'], 'Downloads')
custom_save_folder = DEFAULT_DOWNLOADS

# Dynamic auto-increment naming engine variables
current_prefix = ""           
auto_increment_counter = 1    

# CARUT Theme Colors (#bd4646 Custom Crimson)
BG_COLOR = "#121212"
CARD_COLOR = "#1A1A1A"
PRIMARY_RED = "#bd4646"
HOVER_RED = "#9e3838"
TEXT_MAIN = "#E5E5E5"
TEXT_MUTED = "#888888"
RETRO_FONT = "Courier New" 

ctk.set_appearance_mode("dark")

def get_icon_path():
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, "logo.ico")

def create_fallback_icon():
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    color = PRIMARY_RED if app_active else "#444444"
    draw.rounded_rectangle([10, 20, 54, 55], radius=6, fill=color)
    draw.rectangle([22, 12, 42, 20], fill=color)
    draw.ellipse([24, 27, 40, 43], fill="#121212")
    return image

def get_tray_icon():
    if app_active:
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            try: return Image.open(icon_path)
            except: return create_fallback_icon()
    return create_fallback_icon()

def generate_save_icon():
    img = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, 14, 14], fill=TEXT_MAIN)
    draw.rectangle([11, 2, 14, 5], fill=CARD_COLOR) 
    draw.rectangle([4, 2, 10, 6], fill="#555555")  
    draw.rectangle([4, 9, 12, 14], fill=CARD_COLOR) 
    return ctk.CTkImage(light_image=img, dark_image=img, size=(16, 16))

class StatusWidget(ctk.CTkToplevel):
    """Small persistent desktop tracking indicator locked on the bottom right"""
    def __init__(self, master):
        super().__init__(master)
        self.title("")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("140x35")
        self.configure(fg_color=BG_COLOR)
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"140x35+{screen_w - 160}+{screen_h - 85}")
        
        self.border_frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, border_width=1, border_color=PRIMARY_RED, corner_radius=4)
        self.border_frame.pack(fill="both", expand=True)
        
        self.lbl = ctk.CTkLabel(self.border_frame, text="[CARUT : ON]", font=(RETRO_FONT, 12, "bold"), text_color=PRIMARY_RED)
        self.lbl.pack(expand=True)
        
    def refresh_status(self):
        if app_active:
            self.lbl.configure(text="[CARUT : ON]", text_color=PRIMARY_RED)
            self.border_frame.configure(border_color=PRIMARY_RED)
        else:
            # Drop control switch directly into the shutdown step flow sequence
            self.start_shutdown_countdown(3)

    def start_shutdown_countdown(self, seconds):
        """Ticks down process termination visually before nuking system layers"""
        if seconds > 0:
            self.lbl.configure(text=f"[CARUT : OFF] {seconds}s", text_color=TEXT_MUTED)
            self.border_frame.configure(border_color="#333333")
            self.after(1000, lambda: self.start_shutdown_countdown(seconds - 1))
        else:
            self.withdraw()
            if tray_icon:
                tray_icon.stop()
            self.master.after(0, lambda: [self.master.quit(), os._exit(0)])

class ToastAlert(ctk.CTkToplevel):
    def __init__(self, master, text, is_success=True):
        super().__init__(master)
        self.title("")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.geometry("200x40")
        self.configure(fg_color=BG_COLOR)
        
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        self.geometry(f"200x40+{screen_w - 220}+{screen_h - 135}")
        
        alert_color = PRIMARY_RED if is_success else "#555555"
        frame = ctk.CTkFrame(self, fg_color=CARD_COLOR, border_width=1, border_color=alert_color, corner_radius=6)
        frame.pack(fill="both", expand=True)
        
        lbl = ctk.CTkLabel(frame, text=text, font=(RETRO_FONT, 11, "bold"), text_color=TEXT_MAIN)
        lbl.pack(expand=True)
        
        self.after(2000, self.destroy)

class SavingPanel(ctk.CTkToplevel):
    def __init__(self, master, image_data):
        super().__init__(master)
        self.image_data = image_data
        self.saved_triggered = False 
        
        self.title("CARUT - Saving Panel")
        self.geometry("480x320")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)
        self.attributes("-topmost", True)
        
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (480 // 2)
        y = (self.winfo_screenheight() // 2) - (320 // 2)
        self.geometry(f"480x320+{x}+{y}")

        self.top_border = ctk.CTkFrame(self, height=4, fg_color=PRIMARY_RED, corner_radius=0)
        self.top_border.pack(fill="x", side="top")

        self.main_card = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color="#2A2A2A")
        self.main_card.pack(fill="both", expand=True, padx=15, pady=15)

        self.top_actions_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.top_actions_frame.pack(fill="x", padx=15, pady=(8, 2))
        
        self.header_lbl = ctk.CTkLabel(self.top_actions_frame, text="ASSIGN FILENAME", font=(RETRO_FONT, 12, "bold"), text_color=PRIMARY_RED)
        self.header_lbl.pack(side="left")
        
        self.settings_btn = ctk.CTkButton(
            self.top_actions_frame, text="⚙ Settings", command=self.open_settings, font=(RETRO_FONT, 11),
            fg_color="transparent", text_color=TEXT_MUTED, hover_color="#252525", width=70, height=22
        )
        self.settings_btn.pack(side="right")

        default_name = self.calculate_default_filename()
        self.name_entry = ctk.CTkEntry(
            self.main_card, width=410, height=35, placeholder_text="Enter file name...",
            fg_color="#0F0F0F", border_color="#333333", text_color=TEXT_MAIN, placeholder_text_color="#555555", font=(RETRO_FONT, 12)
        )
        self.name_entry.insert(0, default_name)
        self.name_entry.pack(pady=4)
        
        self.after_idle(self.safe_focus)

        self.format_var = ctk.StringVar(value=".png")
        self.format_dropdown = ctk.CTkComboBox(
            self.main_card, values=[".png", ".jpg", ".jpeg"], variable=self.format_var, width=100, height=28,
            fg_color="#0F0F0F", border_color="#333333", button_color=PRIMARY_RED, button_hover_color=HOVER_RED, text_color=TEXT_MAIN, font=(RETRO_FONT, 11)
        )
        self.format_dropdown.pack(pady=4)

        self.dest_lbl = ctk.CTkLabel(self.main_card, text=f"Target: {self.get_truncated_path()}", font=(RETRO_FONT, 10, "italic"), text_color=TEXT_MUTED)
        self.dest_lbl.pack(pady=2)

        self.btn_row = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.btn_row.pack(pady=(12, 10))

        self.save_button = ctk.CTkButton(
            self.btn_row, text=" Save", image=generate_save_icon(), compound="left", command=self.execute_save, 
            font=(RETRO_FONT, 13, "bold"), fg_color=PRIMARY_RED, hover_color=HOVER_RED, text_color=TEXT_MAIN, height=38, width=130
        )
        self.save_button.pack(side="left", padx=6)

        self.cancel_button = ctk.CTkButton(
            self.btn_row, text="Cancel", command=self.execute_cancel, 
            font=(RETRO_FONT, 13, "bold"), fg_color="#2A2A2A", hover_color="#444444", text_color=TEXT_MAIN, height=38, width=130
        )
        self.cancel_button.pack(side="left", padx=6)
        
        self.bind("<Return>", lambda event: self.execute_save())
        self.bind("<Escape>", lambda event: self.execute_cancel())
        self.protocol("WM_DELETE_WINDOW", self.execute_cancel)

    def safe_focus(self):
        try:
            if self.winfo_exists():
                self.name_entry.focus()
                self.name_entry.select_range(0, 'end')
        except Exception:
            pass

    def calculate_default_filename(self):
        global current_prefix, auto_increment_counter
        if current_prefix:
            return f"{current_prefix}_{auto_increment_counter}"
        else:
            date_today = datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.now().strftime('%H-%M-%S')
            return f"carut-{date_today}_{timestamp}"

    def get_truncated_path(self):
        p = custom_save_folder
        return f"...{p[-35:]}" if len(p) > 38 else p

    def open_settings(self):
        self.withdraw()  
        panel = CoreControlConsole(self.master)
        panel.wait_window()
        self.dest_lbl.configure(text=f"Target: {self.get_truncated_path()}")
        self.deiconify() 

    def execute_save(self):
        global auto_increment_counter, current_prefix
        self.saved_triggered = True
        filename = self.name_entry.get().strip()
        extension = self.format_var.get()
        
        if not filename:
            filename = self.calculate_default_filename()
            
        if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            filename += extension

        save_path = os.path.join(custom_save_folder, filename)
        img = self.image_data
        if filename.lower().endswith(('.jpg', '.jpeg')):
            img = img.convert('RGB')
            
        try:
            img.save(save_path)
            if current_prefix and filename.startswith(current_prefix):
                auto_increment_counter += 1
            ToastAlert(self.master, "✓ Saved Successfully", is_success=True)
        except Exception as error_msg:
            print(f"Write failure error: {error_msg}")
            
        self.destroy()

    def execute_cancel(self):
        if not self.saved_triggered:
            ToastAlert(self.master, "✗ Not Saved", is_success=False)
        self.destroy()

class CoreControlConsole(ctk.CTkToplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("CARUT - Core Control Console")
        self.geometry("450x330")
        self.resizable(False, False)
        self.configure(fg_color=BG_COLOR)
        self.attributes("-topmost", True)
        
        icon_path = get_icon_path()
        if os.path.exists(icon_path):
            self.iconbitmap(icon_path)
        
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (330 // 2)
        self.geometry(f"450x330+{x}+{y}")

        self.top_border = ctk.CTkFrame(self, height=4, fg_color=PRIMARY_RED, corner_radius=0)
        self.top_border.pack(fill="x", side="top")

        self.main_card = ctk.CTkFrame(self, fg_color=CARD_COLOR, corner_radius=8, border_width=1, border_color="#2A2A2A")
        self.main_card.pack(fill="both", expand=True, padx=15, pady=15)

        self.title_lbl = ctk.CTkLabel(self.main_card, text="C A R U T", font=(RETRO_FONT, 20, "bold"), text_color=TEXT_MAIN)
        self.title_lbl.pack(pady=(10, 2))

        self.switch_var = ctk.StringVar(value="on" if app_active else "off")
        self.status_switch = ctk.CTkSwitch(
            self.main_card, text="Redirector Engine Active", command=self.toggle_service,
            variable=self.switch_var, onvalue="on", offvalue="off", font=(RETRO_FONT, 12, "bold"),
            progress_color=PRIMARY_RED, text_color=TEXT_MAIN
        )
        if app_active: self.status_switch.select()
        self.status_switch.pack(pady=8)

        # Prefix UI
        self.prefix_wrapper = ctk.CTkFrame(self.main_card, fg_color="#121212", border_width=1, border_color="#252525", corner_radius=6)
        self.prefix_wrapper.pack(fill="x", padx=15, pady=6)

        self.prefix_title = ctk.CTkLabel(self.prefix_wrapper, text="PRESAVED AUTO-INCREMENT NAME PREFIX", font=(RETRO_FONT, 9, "bold"), text_color=PRIMARY_RED)
        self.prefix_title.pack(pady=(6, 2))

        self.prefix_action_row = ctk.CTkFrame(self.prefix_wrapper, fg_color="transparent")
        self.prefix_action_row.pack(fill="x", padx=10, pady=(2, 6))

        self.prefix_entry = ctk.CTkEntry(
            self.prefix_action_row, height=28, placeholder_text="e.g., compilation (Leave blank)",
            fg_color="#0F0F0F", border_color="#333333", text_color=TEXT_MAIN, font=(RETRO_FONT, 11)
        )
        if current_prefix: self.prefix_entry.insert(0, current_prefix)
        self.prefix_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.apply_prefix_btn = ctk.CTkButton(
            self.prefix_action_row, text="APPLY", command=self.save_prefix, font=(RETRO_FONT, 10, "bold"),
            fg_color=PRIMARY_RED, hover_color=HOVER_RED, text_color=TEXT_MAIN, width=55, height=28
        )
        self.apply_prefix_btn.pack(side="left", padx=2)

        self.reset_prefix_btn = ctk.CTkButton(
            self.prefix_action_row, text="RESET", command=self.reset_prefix, font=(RETRO_FONT, 10, "bold"),
            fg_color="#2A2A2A", hover_color="#444444", text_color=TEXT_MAIN, width=55, height=28
        )
        self.reset_prefix_btn.pack(side="left", padx=2)

        # Folder UI
        self.folder_wrapper = ctk.CTkFrame(self.main_card, fg_color="#121212", border_width=1, border_color="#252525", corner_radius=6)
        self.folder_wrapper.pack(fill="x", padx=15, pady=6)

        self.path_lbl = ctk.CTkLabel(self.folder_wrapper, text=self.get_truncated_path(), font=(RETRO_FONT, 10), text_color=TEXT_MAIN, anchor="w")
        self.path_lbl.pack(fill="x", padx=12, pady=(6, 2))

        self.path_action_row = ctk.CTkFrame(self.folder_wrapper, fg_color="transparent")
        self.path_action_row.pack(fill="x", padx=10, pady=(2, 6))

        self.browse_btn = ctk.CTkButton(
            self.path_action_row, text="BROWSE ROUTE", command=self.change_directory, font=(RETRO_FONT, 10, "bold"),
            fg_color=PRIMARY_RED, hover_color=HOVER_RED, text_color=TEXT_MAIN, height=26
        )
        self.browse_btn.pack(side="left", fill="x", expand=True, padx=(0, 4)) 

        self.reset_path_btn = ctk.CTkButton(
            self.path_action_row, text="RESET TO DOWNLOADS", command=self.reset_directory, font=(RETRO_FONT, 10, "bold"),
            fg_color="#2A2A2A", hover_color="#444444", text_color=TEXT_MAIN, height=26
        )
        self.reset_path_btn.pack(side="right")

    def get_truncated_path(self):
        p = custom_save_folder
        return f"Path: ...{p[-32:]}" if len(p) > 35 else f"Path: {p}"

    def save_prefix(self):
        global current_prefix, auto_increment_counter
        current_prefix = self.prefix_entry.get().strip()
        auto_increment_counter = 1

    def reset_prefix(self):
        global current_prefix, auto_increment_counter
        current_prefix = ""
        auto_increment_counter = 1
        self.prefix_entry.delete(0, 'end')

    def change_directory(self):
        global custom_save_folder
        selected_dir = filedialog.askdirectory(initialdir=custom_save_folder, title="Select CARUT Save Destination")
        if selected_dir:
            custom_save_folder = os.path.abspath(selected_dir)
            self.path_lbl.configure(text=self.get_truncated_path())

    def reset_directory(self):
        global custom_save_folder
        custom_save_folder = DEFAULT_DOWNLOADS
        self.path_lbl.configure(text=self.get_truncated_path())

    def toggle_service(self):
        global app_active, tray_icon, status_widget_instance
        if self.switch_var.get() == "on":
            app_active = True
            tray_icon.title = "CARUT: Active"
            tray_icon.icon = get_tray_icon()
            if status_widget_instance:
                status_widget_instance.refresh_status()
        else:
            app_active = False
            tray_icon.title = "CARUT: Inactive"
            tray_icon.icon = get_tray_icon()
            
            # Instantly drop console structure layout to uncover desktop tracking elements
            self.destroy() 
            
            if status_widget_instance:
                status_widget_instance.refresh_status()

def monitor_clipboard():
    last_image = None
    while True:
        try:
            if app_active:
                current_image = ImageGrab.grabclipboard()
                if current_image is not None:
                    if last_image is None or not is_same_image(current_image, last_image):
                        if main_root:
                            main_root.after(0, lambda img=current_image: SavingPanel(main_root, img))
                        last_image = current_image
        except Exception:
            pass
        time.sleep(0.4)

def is_same_image(img1, img2):
    try:
        if img1.size != img2.size or img1.mode != img2.mode: return False
        return ImageChops.difference(img1, img2).getbbox() is None
    except Exception: return False

def start_tray_thread():
    global tray_icon
    menu = pystray.Menu(
        item('Open CARUT Panel', lambda: main_root.after(0, lambda: CoreControlConsole(main_root)), default=True),
        item('Exit System Utility', lambda icon, item: [icon.stop(), main_root.after(0, main_root.quit)])
    )
    tray_icon = pystray.Icon("carut_tool", get_tray_icon(), "CARUT: Active", menu)
    tray_icon.run()

if __name__ == "__main__":
    main_root = ctk.CTk()
    main_root.withdraw() 
    
    icon_path = get_icon_path()
    if os.path.exists(icon_path):
        main_root.iconbitmap(icon_path)

    status_widget_instance = StatusWidget(main_root)
    
    threading.Thread(target=start_tray_thread, daemon=True).start()
    threading.Thread(target=monitor_clipboard, daemon=True).start()

    main_root.mainloop()
    os._exit(0)