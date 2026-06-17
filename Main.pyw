import customtkinter as ctk
import cv2
import pyttsx3
import os
import sys
from datetime import datetime as dt
import time
import csv
import qrcode
from PIL import Image, ImageTk
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

current_dir = os.getcwd()
os.chdir(current_dir)

data_file = "data.csv"

# Ensure data.csv exists with headers
if not os.path.exists(data_file):
    with open(data_file, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Student ID", "Course Name", "Date", "Total Attended"])

class QRResult:
    """Mimics pyzbar's object with a `.data` attribute (bytes)."""
    def __init__(self, data, points):
        self.data = data.encode("utf-8")  # make it bytes like pyzbar
        self.points = points

def custom_decode(frame):
    """
    Detects and decodes QR codes in the given frame using OpenCV.
    Returns a list of QRResult objects.
    """
    qr_detector = cv2.QRCodeDetector()
    results = []

    # Try multi-detection
    try:
        retval, decoded_info, points, _ = qr_detector.detectAndDecodeMulti(frame)
        if retval:
            for data, pts in zip(decoded_info, points):
                if data:
                    results.append(QRResult(data, pts))
        else:
            # fallback single detection
            data, pts, _ = qr_detector.detectAndDecode(frame)
            if data:
                results.append(QRResult(data, pts))
    except Exception as e:
        print("Decode error:", e)

    return results

def count_attendance(student_id, course_name):
    try:
        if not os.path.exists(data_file):
            return 1
        
        unique_dates = set()
        with open(data_file, "r") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) >= 3 and row[0] == student_id and row[1] == course_name:
                    unique_dates.add(row[2])
        
        return len(unique_dates) + 1
    except Exception as e:
        print("Count error:", e)
        return 1

def is_duplicate(student_id, course_name, date):
    try:
        if not os.path.exists(data_file):
            return False
        with open(data_file, "r") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if len(row) >= 3 and row[0] == student_id and row[1] == course_name and row[2] == date:
                    return True
        return False
    except Exception as e:
        print("Duplicate check error:", e)
        return False

def capture(frame, file_name):
    try:
        folder_name = "Captured Images"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        img_path = os.path.join(folder_name, file_name)
        cv2.imwrite(img_path, frame)
    except Exception as e:
        print("Capture error:", e)

def registry_qr(student_id):
    """Generates a QR code for the given Student ID and returns the file path."""
    try:
        set_id = student_id.strip()
        if not set_id:
            return None

        img = qrcode.make(set_id)
        folder_name = "Student QR"
        file_name = f"{set_id}.png"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        QR_link = os.path.join(folder_name, file_name)
        img.save(QR_link)
        return QR_link
    except Exception as e:
        print("QR Generation error:", e)
        return None

def run_voice_feedback(text):
    """Runs speak functionality. Executed in a thread to keep GUI responsive."""
    try:
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print("Voice engine error:", e)

def speak_async(text):
    """Starts background thread to read text aloud."""
    threading.Thread(target=run_voice_feedback, args=(text,), daemon=True).start()

def import_csv_students(file_path, progress_callback=None):
    """Reads a CSV file and registers students automatically."""
    try:
        with open(file_path, 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
        if not rows:
            return 0, "Selected CSV file is empty."
        
        # Determine if CSV has a header
        header = rows[0]
        id_col_index = -1
        
        # Search for known student ID header labels
        potential_headers = ["student id", "studentid", "id", "roll no", "roll number", "roll_no", "student_id", "student"]
        for idx, col in enumerate(header):
            cleaned_col = str(col).strip().lower()
            if cleaned_col in potential_headers:
                id_col_index = idx
                break
        
        has_header = False
        if id_col_index != -1:
            has_header = True
        else:
            # Fallback: check if the first row values are completely non-numeric. 
            # If so, it's likely a header. If they are numeric, treat first row as data.
            is_numeric = all(item.strip().isdigit() for item in header if item.strip())
            if not is_numeric:
                has_header = True
            id_col_index = 0  # Fallback to column index 0
            
        start_row = 1 if has_header else 0
        data_rows = rows[start_row:]
        
        success_count = 0
        total_rows = len(data_rows)
        
        for idx, row in enumerate(data_rows):
            if not row or len(row) <= id_col_index:
                continue
            student_id = str(row[id_col_index]).strip()
            if student_id and student_id.isdigit():
                registry_qr(student_id)
                success_count += 1
            if progress_callback:
                progress_callback(idx + 1, total_rows)
                
        return success_count, f"Successfully registered {success_count} students from CSV!"
    except Exception as e:
        return 0, f"Error processing CSV: {str(e)}"


class SmartAttendanceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Set overall styling
        ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
        ctk.set_default_color_theme("blue")
        
        self.title("Smart Attendance Management System")
        self.geometry("1100x680")
        self.minsize(1000, 620)
        
        # Set window close handler
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Application state variables
        self.is_scanning = False
        self.cap = None
        self.last_scan_id = ""
        self.last_scan_time = 0.0
        
        # Configure layout (2 columns: Sidebar & Main Content)
        self.grid_columnconfigure(0, weight=0, minsize=240)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # 1. CREATE SIDEBAR
        self.sidebar_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=("#f1f5f9", "#0f172a"))
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(7, weight=1) # Spacer
        
        # Sidebar Logo / Title
        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="🎓 Smart Attendance", 
                                       font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
                                       text_color=("#0f172a", "#3b82f6"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 30), sticky="w")
        
        # Sidebar Navigation Buttons
        self.nav_buttons = {}
        tabs = [
            ("dashboard", "🏠 Dashboard"),
            ("register", "👤 Student Registration"),
            ("take_attendance", "📋 Take Attendance"),
            ("records", "📊 Attendance Records"),
            ("settings", "⚙️ System Settings")
        ]
        
        for idx, (tab_id, label) in enumerate(tabs):
            btn = ctk.CTkButton(self.sidebar_frame, text=label, 
                                font=ctk.CTkFont(family="Segoe UI", size=13, weight="normal"),
                                height=45, corner_radius=8, anchor="w", fg_color="transparent",
                                text_color=("#334155", "#94a3b8"), hover_color=("#e2e8f0", "#1e293b"),
                                command=lambda t=tab_id: self.select_tab(t))
            btn.grid(row=idx+1, column=0, padx=15, pady=6, sticky="ew")
            self.nav_buttons[tab_id] = btn
            
        # Sidebar Theme Selector
        self.theme_label = ctk.CTkLabel(self.sidebar_frame, text="Theme:", 
                                        font=ctk.CTkFont(family="Segoe UI", size=12),
                                        text_color=("#64748b", "#64748b"))
        self.theme_label.grid(row=8, column=0, padx=20, pady=(10, 2), sticky="w")
        
        self.theme_menu = ctk.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"],
                                            font=ctk.CTkFont(family="Segoe UI", size=12),
                                            command=self.change_theme)
        self.theme_menu.grid(row=9, column=0, padx=15, pady=(0, 25), sticky="ew")
        
        # 2. CREATE PAGE FRAMES
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)
        
        self.frames = {
            "dashboard": self.create_dashboard_frame(),
            "register": self.create_register_frame(),
            "take_attendance": self.create_attendance_frame(),
            "records": self.create_records_frame(),
            "settings": self.create_settings_frame()
        }
        
        # Select default tab
        self.select_tab("dashboard")
        
    def select_tab(self, tab_id):
        # Stop scanner if moving away from take_attendance
        if tab_id != "take_attendance" and self.is_scanning:
            self.stop_scanner()
            
        # Hide all frames
        for frame in self.frames.values():
            frame.grid_forget()
            
        # Reset all button styles
        for tid, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent", text_color=("#334155", "#94a3b8"))
            
        # Highlight active button
        self.nav_buttons[tab_id].configure(fg_color=("#3b82f6", "#1e293b"), text_color=("#ffffff", "#3b82f6"))
        
        # Display selected frame
        self.frames[tab_id].grid(row=0, column=0, sticky="nsew")
        
        # Run callbacks
        if tab_id == "dashboard":
            self.refresh_dashboard()
        elif tab_id == "records":
            self.load_attendance_records()
            
    def change_theme(self, new_mode):
        ctk.set_appearance_mode(new_mode)
        # Treeview styles need to adapt to light/dark background colors
        self.after(50, self.update_treeview_styles)

    def on_closing(self):
        try:
            self.is_scanning = False
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
        except:
            pass
        self.destroy()

    # ------------------ TAB FRAME CREATORS ------------------
    
    def create_dashboard_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure((0, 1, 2), weight=1, pad=15)
        frame.grid_rowconfigure(1, weight=1)
        
        # Page title
        title = ctk.CTkLabel(frame, text="System Dashboard", 
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky="w")
        
        # Card 1: Registered Students
        self.card_reg = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.card_reg.grid(row=1, column=0, sticky="nsew", pady=10, padx=5)
        self.card_reg.grid_columnconfigure(0, weight=1)
        
        lbl_reg_title = ctk.CTkLabel(self.card_reg, text="Registered Students", font=ctk.CTkFont("Segoe UI", 13, "normal"), text_color=("#64748b", "#94a3b8"))
        lbl_reg_title.pack(pady=(20, 5))
        self.lbl_reg_count = ctk.CTkLabel(self.card_reg, text="0", font=ctk.CTkFont("Segoe UI", 38, "bold"), text_color=("#0f172a", "#f8fafc"))
        self.lbl_reg_count.pack(pady=(0, 20))
        
        # Card 2: Total Logs
        self.card_logs = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.card_logs.grid(row=1, column=1, sticky="nsew", pady=10, padx=5)
        self.card_logs.grid_columnconfigure(0, weight=1)
        
        lbl_logs_title = ctk.CTkLabel(self.card_logs, text="Total Records", font=ctk.CTkFont("Segoe UI", 13, "normal"), text_color=("#64748b", "#94a3b8"))
        lbl_logs_title.pack(pady=(20, 5))
        self.lbl_logs_count = ctk.CTkLabel(self.card_logs, text="0", font=ctk.CTkFont("Segoe UI", 38, "bold"), text_color=("#0f172a", "#f8fafc"))
        self.lbl_logs_count.pack(pady=(0, 20))
        
        # Card 3: Today's Scans
        self.card_today = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.card_today.grid(row=1, column=2, sticky="nsew", pady=10, padx=5)
        self.card_today.grid_columnconfigure(0, weight=1)
        
        lbl_today_title = ctk.CTkLabel(self.card_today, text="Attendance Recorded Today", font=ctk.CTkFont("Segoe UI", 13, "normal"), text_color=("#64748b", "#94a3b8"))
        lbl_today_title.pack(pady=(20, 5))
        self.lbl_today_count = ctk.CTkLabel(self.card_today, text="0", font=ctk.CTkFont("Segoe UI", 38, "bold"), text_color=("#0f172a", "#f8fafc"))
        self.lbl_today_count.pack(pady=(0, 20))
        
        # Bottom section: Recent Activities
        self.recent_frame = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        self.recent_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=(15, 10))
        self.recent_frame.grid_columnconfigure(0, weight=1)
        
        lbl_recent_title = ctk.CTkLabel(self.recent_frame, text="🕒 Recent Attendance Scans", font=ctk.CTkFont("Segoe UI", 15, "bold"))
        lbl_recent_title.pack(anchor="w", padx=20, pady=(15, 10))
        
        self.scroll_logs = ctk.CTkScrollableFrame(self.recent_frame, fg_color="transparent", height=240)
        self.scroll_logs.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        return frame
        
    def refresh_dashboard(self):
        # Count Registered Students
        reg_count = 0
        try:
            if os.path.exists("Student QR"):
                reg_count = len([f for f in os.listdir("Student QR") if f.endswith(".png")])
        except Exception as e:
            print(e)
            
        # Parse Logs
        total_logs = 0
        today_scans = 0
        recent_entries = []
        today_str = dt.now().strftime('%d_%m_%Y')
        
        try:
            if os.path.exists(data_file):
                with open(data_file, "r") as f:
                    reader = csv.reader(f)
                    next(reader, None)  # Skip header
                    all_rows = list(reader)
                    total_logs = len(all_rows)
                    today_scans = sum(1 for row in all_rows if len(row) >= 3 and row[2] == today_str)
                    
                    # Reverse list to get the most recent scans first
                    for row in reversed(all_rows):
                        if len(row) >= 4:
                            recent_entries.append(row)
        except Exception as e:
            print(e)
            
        # Update UI text
        self.lbl_reg_count.configure(text=str(reg_count))
        self.lbl_logs_count.configure(text=str(total_logs))
        self.lbl_today_count.configure(text=str(today_scans))
        
        # Clear recent scan cards
        for widget in self.scroll_logs.winfo_children():
            widget.destroy()
            
        if not recent_entries:
            placeholder = ctk.CTkLabel(self.scroll_logs, text="No attendance scans recorded yet. Go to 'Take Attendance' to begin.", 
                                       font=ctk.CTkFont("Segoe UI", 12, slant="italic"), text_color="#64748b")
            placeholder.pack(pady=30)
        else:
            for idx, entry in enumerate(recent_entries[:8]): # Show last 8 records
                student_id, course_name, scan_date, total = entry[0], entry[1], entry[2], entry[3]
                
                # Container row for each log
                log_row = ctk.CTkFrame(self.scroll_logs, fg_color=("#f8fafc", "#0f172a") if idx % 2 == 0 else "transparent", corner_radius=6)
                log_row.pack(fill="x", pady=2, ipady=4)
                
                txt = f"  ✅ Student ID: {student_id}  |  Course: {course_name}  |  Date: {scan_date}  |  Total Days Attended: {total}"
                lbl = ctk.CTkLabel(log_row, text=txt, font=ctk.CTkFont("Segoe UI", 12, "normal"), anchor="w")
                lbl.pack(fill="x", padx=10, pady=4)

    def create_register_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure((0, 1), weight=1, pad=20)
        frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(frame, text="Student Registration Portal", 
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
        
        # Column 0: Single Registration Card
        card_single = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_single.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        card_single.grid_columnconfigure(0, weight=1)
        
        lbl_single_title = ctk.CTkLabel(card_single, text="👤 Register Single Student", font=ctk.CTkFont("Segoe UI", 16, "bold"))
        lbl_single_title.pack(anchor="w", padx=20, pady=(20, 5))
        lbl_single_desc = ctk.CTkLabel(card_single, text="Enter a numerical ID to automatically generate a student QR code.", 
                                       font=ctk.CTkFont("Segoe UI", 12), text_color=("#64748b", "#94a3b8"), wraplength=350, justify="left")
        lbl_single_desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        self.ent_single_id = ctk.CTkEntry(card_single, placeholder_text="Enter Student ID (e.g. 104523)", height=40, font=ctk.CTkFont("Segoe UI", 12))
        self.ent_single_id.pack(fill="x", padx=20, pady=(0, 15))
        
        btn_single_submit = ctk.CTkButton(card_single, text="Register Student", font=ctk.CTkFont("Segoe UI", 13, "bold"), 
                                          height=40, fg_color=("#10b981", "#059669"), hover_color=("#059669", "#047857"),
                                          command=self.on_single_register)
        btn_single_submit.pack(fill="x", padx=20, pady=(0, 20))
        
        # QR Preview Container
        preview_border = ctk.CTkFrame(card_single, fg_color=("#f8fafc", "#0f172a"), height=200, corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"))
        preview_border.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        preview_border.pack_propagate(False)
        
        self.qr_preview_label = ctk.CTkLabel(preview_border, text="QR Code Preview\nWill display here", font=ctk.CTkFont("Segoe UI", 12, slant="italic"), text_color="#64748b")
        self.qr_preview_label.pack(expand=True)
        
        # Column 1: Bulk CSV Registration Card
        card_bulk = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_bulk.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        card_bulk.grid_columnconfigure(0, weight=1)
        
        lbl_bulk_title = ctk.CTkLabel(card_bulk, text="📁 Bulk CSV Registration", font=ctk.CTkFont("Segoe UI", 16, "bold"))
        lbl_bulk_title.pack(anchor="w", padx=20, pady=(20, 5))
        lbl_bulk_desc = ctk.CTkLabel(card_bulk, text="Upload a spreadsheet containing student IDs to automatically register multiple QR codes in bulk.", 
                                     font=ctk.CTkFont("Segoe UI", 12), text_color=("#64748b", "#94a3b8"), wraplength=350, justify="left")
        lbl_bulk_desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        # CSV requirements block
        req_frame = ctk.CTkFrame(card_bulk, fg_color=("#f8fafc", "#0f172a"), corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"))
        req_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        req_text = "💡 CSV File Requirements:\n• Rows must contain numerical Student IDs.\n• Auto-scans headers: 'Student ID', 'ID', 'Roll No', etc.\n• If no header matches, first column will be imported."
        lbl_req = ctk.CTkLabel(req_frame, text=req_text, font=ctk.CTkFont("Segoe UI", 12), text_color=("#334155", "#cbd5e1"), justify="left", anchor="w")
        lbl_req.pack(padx=15, pady=15)
        
        btn_bulk_submit = ctk.CTkButton(card_bulk, text="📁 Choose CSV File & Register", font=ctk.CTkFont("Segoe UI", 13, "bold"), 
                                        height=45, fg_color=("#3b82f6", "#2563eb"), hover_color=("#2563eb", "#1d4ed8"),
                                        command=self.on_bulk_register)
        btn_bulk_submit.pack(fill="x", padx=20, pady=(0, 20))
        
        # Bulk status / progress bar
        self.bulk_progress = ctk.CTkProgressBar(card_bulk, mode="determinate", height=10)
        self.bulk_progress.pack(fill="x", padx=20, pady=(0, 10))
        self.bulk_progress.grid_forget() # Hide initially
        
        self.bulk_status_label = ctk.CTkLabel(card_bulk, text="", font=ctk.CTkFont("Segoe UI", 12), text_color=("#475569", "#94a3b8"), wraplength=350)
        self.bulk_status_label.pack(padx=20, pady=(0, 20))
        
        return frame
        
    def on_single_register(self):
        input_val = self.ent_single_id.get().strip()
        if not input_val:
            messagebox.showerror("Validation Error", "Student ID cannot be empty!")
            return
            
        if not input_val.isdigit():
            messagebox.showerror("Validation Error", "Student ID must contain only numbers!")
            return
            
        # Generate QR code
        qr_path = registry_qr(input_val)
        if qr_path and os.path.exists(qr_path):
            self.ent_single_id.delete(0, 'end')
            
            # Show preview
            try:
                pil_img = Image.open(qr_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(180, 180))
                self.qr_preview_label.configure(image=ctk_img, text="")
                self.qr_preview_label.image = ctk_img
            except Exception as e:
                print("Failed to display QR code preview:", e)
                
            messagebox.showinfo("Success", f"Student ID '{input_val}' registered successfully!\nQR code saved in 'Student QR' folder.")
            speak_async("Registration successful")
            self.refresh_dashboard()
        else:
            messagebox.showerror("Execution Error", "An error occurred while generating the QR code.")

    def on_bulk_register(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if not filepath:
            return
            
        # Start importing in a background thread to prevent UI freezing
        threading.Thread(target=self.bulk_register_thread, args=(filepath,), daemon=True).start()
        
    def bulk_register_thread(self, filepath):
        try:
            # Update UI on Main Thread
            def progress_cb(current, total):
                val = current / total
                self.after(0, lambda: self.bulk_progress.set(val))
                self.after(0, lambda: self.bulk_status_label.configure(
                    text=f"Processed: {current} of {total} records...", text_color=("#3b82f6", "#60a5fa")))
            
            self.after(0, lambda: self.bulk_progress.grid()) # Show
            self.after(0, lambda: self.bulk_progress.set(0))
            self.after(0, lambda: self.bulk_status_label.configure(text="Reading CSV file...", text_color=("#475569", "#94a3b8")))
            
            success_count, msg = import_csv_students(filepath, progress_cb)
            
            # Reset progress updates on Main Thread
            self.after(0, lambda: self.bulk_progress.grid_forget())
            self.after(0, lambda: self.bulk_status_label.configure(text=f"✅ {msg}", text_color=("#10b981", "#34d399")))
            self.after(0, lambda: messagebox.showinfo("Import Complete", f"Bulk registration complete! {success_count} students registered."))
            
            speak_async("Bulk registration complete")
            self.after(0, self.refresh_dashboard)
        except Exception as e:
            self.after(0, lambda: self.bulk_progress.grid_forget())
            self.after(0, lambda: self.bulk_status_label.configure(text=f"❌ Error: {str(e)}", text_color="#ef4444"))
            self.after(0, lambda: messagebox.showerror("Import Error", f"An error occurred: {str(e)}"))

    def create_attendance_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=0, minsize=320)
        frame.grid_columnconfigure(1, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Page Title
        title = ctk.CTkLabel(frame, text="Take Attendance Scanner", 
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
        
        # Left Control Panel
        card_control = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_control.grid(row=1, column=0, sticky="nsew", padx=(0, 10), pady=5)
        card_control.grid_columnconfigure(0, weight=1)
        
        lbl_ctrl_title = ctk.CTkLabel(card_control, text="📋 Scanner Controls", font=ctk.CTkFont("Segoe UI", 16, "bold"))
        lbl_ctrl_title.pack(anchor="w", padx=20, pady=(20, 15))
        
        lbl_course = ctk.CTkLabel(card_control, text="Course Name", font=ctk.CTkFont("Segoe UI", 12, "normal"), text_color=("#475569", "#94a3b8"))
        lbl_course.pack(anchor="w", padx=20, pady=(0, 4))
        
        self.ent_course = ctk.CTkEntry(card_control, placeholder_text="Enter Course Name (e.g. Physics-I)", height=40)
        self.ent_course.pack(fill="x", padx=20, pady=(0, 15))
        
        lbl_cam = ctk.CTkLabel(card_control, text="Camera Source", font=ctk.CTkFont("Segoe UI", 12, "normal"), text_color=("#475569", "#94a3b8"))
        lbl_cam.pack(anchor="w", padx=20, pady=(0, 4))
        
        self.menu_cam = ctk.CTkOptionMenu(card_control, values=["Camera 0", "Camera 1", "Camera 2"], height=40)
        self.menu_cam.pack(fill="x", padx=20, pady=(0, 20))
        
        self.btn_scan = ctk.CTkButton(card_control, text="Start Scanner", font=ctk.CTkFont("Segoe UI", 13, "bold"), 
                                      height=45, fg_color=("#3b82f6", "#2563eb"), hover_color=("#2563eb", "#1d4ed8"),
                                      command=self.toggle_scanner)
        self.btn_scan.pack(fill="x", padx=20, pady=(0, 20))
        
        # Live Scan Status Card
        status_box = ctk.CTkFrame(card_control, fg_color=("#f8fafc", "#0f172a"), corner_radius=8, border_width=1, border_color=("#e2e8f0", "#334155"))
        status_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        status_box.grid_columnconfigure(0, weight=1)
        status_box.grid_rowconfigure(0, weight=1)
        
        self.scanner_status_val = ctk.CTkLabel(status_box, text="Scanner Inactive\n\nConfigure settings and click 'Start Scanner'.", 
                                               font=ctk.CTkFont("Segoe UI", 12, "normal"), text_color="#64748b", wraplength=260)
        self.scanner_status_val.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        # Right Camera Viewport
        self.card_camera = ctk.CTkFrame(frame, fg_color="#000000", corner_radius=12, border_width=1, border_color="#334155")
        self.card_camera.grid(row=1, column=1, sticky="nsew", padx=(10, 0), pady=5)
        self.card_camera.grid_columnconfigure(0, weight=1)
        self.card_camera.grid_rowconfigure(0, weight=1)
        
        self.camera_label = ctk.CTkLabel(self.card_camera, text="Webcam Feed Live-Preview Area\n\nStart scanner to connect webcam.", 
                                         font=ctk.CTkFont("Segoe UI", 14, "normal"), text_color="#64748b")
        self.camera_label.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        return frame
        
    def toggle_scanner(self):
        if not self.is_scanning:
            # Validate Course Name
            course_name = self.ent_course.get().strip()
            if not course_name:
                messagebox.showerror("Input Error", "Please enter a Course Name first!")
                return
                
            # Parse camera source
            cam_str = self.menu_cam.get()
            try:
                cam_idx = int(cam_str.split(" ")[-1])
            except:
                cam_idx = 0
                
            # Open video stream
            self.cap = cv2.VideoCapture(cam_idx)
            if not self.cap.isOpened():
                messagebox.showerror("Hardware Error", "Could not connect to the selected camera. Please verify device connection.")
                return
                
            # Update state and UI
            self.is_scanning = True
            self.current_course = course_name
            self.btn_scan.configure(text="Stop Scanner", fg_color=("#ef4444", "#dc2626"), hover_color=("#dc2626", "#b91c1c"))
            self.scanner_status_val.configure(text="📷 Camera Active\nHold student QR code steadily in front of the lens.", text_color=("#3b82f6", "#60a5fa"))
            self.ent_course.configure(state="disabled")
            self.menu_cam.configure(state="disabled")
            
            # Start loop
            self.update_webcam_feed()
        else:
            self.stop_scanner()

    def stop_scanner(self):
        self.is_scanning = False
        if self.cap:
            self.cap.release()
            self.cap = None
            
        # Reset UI
        self.btn_scan.configure(text="Start Scanner", fg_color=("#3b82f6", "#2563eb"), hover_color=("#2563eb", "#1d4ed8"))
        self.scanner_status_val.configure(text="Scanner Inactive\n\nConfigure settings and click 'Start Scanner'.", text_color="#64748b")
        self.camera_label.configure(image=None, text="Webcam Feed Live-Preview Area\n\nStart scanner to connect webcam.")
        self.camera_label.image = None
        self.ent_course.configure(state="normal")
        self.menu_cam.configure(state="normal")
        
    def record_attendance_db(self, student_id, course_name, current_date):
        """Records student attendance in database. Returns (success, total)."""
        try:
            total = count_attendance(student_id, course_name)
            if not is_duplicate(student_id, course_name, current_date):
                with open(data_file, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([student_id, course_name, current_date, total])
                return True, total
            else:
                return False, total
        except Exception as e:
            print("Database error:", e)
            return None, 0

    def update_webcam_feed(self):
        if not self.is_scanning or self.cap is None:
            return
            
        ret, frame = self.cap.read()
        if ret:
            now = time.time()
            
            # Perform QR code detection
            qr_results = custom_decode(frame)
            if qr_results:
                for qr in qr_results:
                    student_id = qr.data.decode('utf-8').strip()
                    if student_id:
                        # Debounce/Cooldown: avoid rapid recording of same ID (cooldown of 3 seconds)
                        if student_id != self.last_scan_id or (now - self.last_scan_time > 3.0):
                            self.last_scan_id = student_id
                            self.last_scan_time = now
                            
                            # Capture and record data
                            date_str = dt.now().strftime('%d_%m_%Y')
                            img_filename = f"{date_str}_{student_id}.jpg"
                            capture(frame, img_filename)
                            
                            success, total_attended = self.record_attendance_db(student_id, self.current_course, date_str)
                            
                            if success:
                                txt_msg = f"✅ Student: {student_id} marked!\nTotal Days Attended: {total_attended}"
                                color = ("#10b981", "#34d399")
                                voice_phrase = f"Attendance marked for student {student_id}"
                            elif success is False:
                                txt_msg = f"⚠️ Student: {student_id} already marked today."
                                color = ("#f59e0b", "#fbbf24")
                                voice_phrase = "Duplicate entry"
                            else:
                                txt_msg = "❌ Error writing to attendance database."
                                color = "#ef4444"
                                voice_phrase = "Database error"
                                
                            self.scanner_status_val.configure(text=txt_msg, text_color=color)
                            speak_async(voice_phrase)
                            self.refresh_dashboard()
                            break # Handle one scan per frame
            
            # Convert frame format and render on UI label
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            
            # Match camera viewport frame size (~ 500 x 375 is clean aspect ratio)
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(500, 375))
            self.camera_label.configure(image=ctk_img, text="")
            self.camera_label.image = ctk_img
            
        self.after(10, self.update_webcam_feed)

    def create_records_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)
        
        # Page Title
        title = ctk.CTkLabel(frame, text="Attendance Log Viewer", 
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
        title.grid(row=0, column=0, pady=(0, 20), sticky="w")
        
        # Search & Action Container
        search_card = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        search_card.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        lbl_search = ctk.CTkLabel(search_card, text="🔍 Search:", font=ctk.CTkFont("Segoe UI", 12, "bold"))
        lbl_search.pack(side="left", padx=(15, 5), pady=12)
        
        self.search_entry = ctk.CTkEntry(search_card, placeholder_text="Filter by Student ID or Course Name...", width=320)
        self.search_entry.pack(side="left", padx=5, pady=12)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_attendance_records())
        
        btn_clear_search = ctk.CTkButton(search_card, text="Clear", width=80, fg_color=("#e2e8f0", "#334155"), 
                                         text_color=("#0f172a", "#f1f5f9"), hover_color=("#cbd5e1", "#475569"),
                                         command=self.clear_search)
        btn_clear_search.pack(side="left", padx=5, pady=12)
        
        btn_refresh = ctk.CTkButton(search_card, text="⟲ Refresh Logs", width=120, fg_color=("#3b82f6", "#2563eb"),
                                    hover_color=("#2563eb", "#1d4ed8"), command=self.load_attendance_records)
        btn_refresh.pack(side="right", padx=15, pady=12)
        
        # Spreadsheet Container Frame
        table_card = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        table_card.grid(row=2, column=0, sticky="nsew")
        table_card.grid_columnconfigure(0, weight=1)
        table_card.grid_rowconfigure(0, weight=1)
        
        # Setup standard Tkinter Treeview inside a container frame
        self.tree_container = tk.Frame(table_card, bg="#ffffff")
        self.tree_container.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.tree_container.grid_columnconfigure(0, weight=1)
        self.tree_container.grid_rowconfigure(0, weight=1)
        
        columns = ("StudentID", "CourseName", "Date", "TotalAttended")
        self.tree = ttk.Treeview(self.tree_container, columns=columns, show="headings", selectmode="browse")
        self.tree.grid(row=0, column=0, sticky="nsew")
        
        # Setup Column Headers
        self.tree.heading("StudentID", text="Student ID")
        self.tree.heading("CourseName", text="Course Name")
        self.tree.heading("Date", text="Date Recorded")
        self.tree.heading("TotalAttended", text="Total Days Attended")
        
        self.tree.column("StudentID", anchor="center", width=150)
        self.tree.column("CourseName", anchor="w", width=250)
        self.tree.column("Date", anchor="center", width=150)
        self.tree.column("TotalAttended", anchor="center", width=180)
        
        # Scrollbars
        v_scroll = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        h_scroll = ttk.Scrollbar(self.tree_container, orient="horizontal", command=self.tree.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        self.tree.configure(xscrollcommand=h_scroll.set)
        
        # Load Treeview Styling
        self.update_treeview_styles()
        
        return frame
        
    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.load_attendance_records()
        
    def update_treeview_styles(self):
        # Dynamically set colors based on light/dark mode
        mode = ctk.get_appearance_mode().lower()
        style = ttk.Style()
        style.theme_use("clam")
        
        if mode == "dark":
            bg = "#1e293b"       # slate-800
            fg = "#f8fafc"       # slate-50
            field_bg = "#1e293b"
            header_bg = "#0f172a" # slate-900
            header_fg = "#3b82f6"
            selected_bg = "#3b82f6"
            selected_fg = "#ffffff"
            frame_bg = "#1e293b"
        else:
            bg = "#ffffff"
            fg = "#0f172a"
            field_bg = "#ffffff"
            header_bg = "#e2e8f0" # slate-200
            header_fg = "#1e293b"
            selected_bg = "#3b82f6"
            selected_fg = "#ffffff"
            frame_bg = "#ffffff"
            
        self.tree_container.configure(bg=frame_bg)
        
        style.configure("Treeview", 
                        background=bg, 
                        foreground=fg, 
                        rowheight=30,
                        fieldbackground=field_bg,
                        font=("Segoe UI", 11))
        
        style.configure("Treeview.Heading",
                        background=header_bg,
                        foreground=header_fg,
                        font=("Segoe UI", 11, "bold"),
                        borderwidth=1)
        
        style.map("Treeview",
                  background=[("selected", selected_bg)],
                  foreground=[("selected", selected_fg)])
                  
    def load_attendance_records(self):
        # Clear Treeview rows
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not os.path.exists(data_file):
            return
            
        search_filter = self.search_entry.get().strip().lower()
        
        try:
            with open(data_file, "r") as file:
                reader = csv.reader(file)
                next(reader, None) # Skip header
                for row in reader:
                    if len(row) < 4:
                        continue
                    student_id, course_name, date_str, total_attended = row[0], row[1], row[2], row[3]
                    
                    # Apply filter
                    if search_filter:
                        if search_filter not in student_id.lower() and search_filter not in course_name.lower():
                            continue
                            
                    self.tree.insert("", "end", values=(student_id, course_name, date_str, total_attended))
        except Exception as e:
            print("Error loading records:", e)

    def create_settings_frame(self):
        frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        frame.grid_columnconfigure((0, 1), weight=1, pad=15)
        frame.grid_rowconfigure(1, weight=1)
        
        # Title
        title = ctk.CTkLabel(frame, text="System Configurations", 
                             font=ctk.CTkFont(family="Segoe UI", size=24, weight="bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky="w")
        
        # Column 0: Folder shortcuts and Directories
        card_dir = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_dir.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        card_dir.grid_columnconfigure(0, weight=1)
        
        lbl_dir_title = ctk.CTkLabel(card_dir, text="📁 Local Folders Access", font=ctk.CTkFont("Segoe UI", 16, "bold"))
        lbl_dir_title.pack(anchor="w", padx=20, pady=(20, 5))
        lbl_dir_desc = ctk.CTkLabel(card_dir, text="Open system directories directly in Windows Explorer.", 
                                     font=ctk.CTkFont("Segoe UI", 12), text_color=("#64748b", "#94a3b8"))
        lbl_dir_desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        btn_open_qr = ctk.CTkButton(card_dir, text="📁 Open Student QR Folder", font=ctk.CTkFont("Segoe UI", 12, "normal"), 
                                    height=40, fg_color=("#e2e8f0", "#334155"), text_color=("#0f172a", "#f1f5f9"), hover_color=("#cbd5e1", "#475569"),
                                    command=lambda: self.open_local_path("Student QR"))
        btn_open_qr.pack(fill="x", padx=20, pady=8)
        
        btn_open_imgs = ctk.CTkButton(card_dir, text="📷 Open Captured Images Folder", font=ctk.CTkFont("Segoe UI", 12, "normal"), 
                                      height=40, fg_color=("#e2e8f0", "#334155"), text_color=("#0f172a", "#f1f5f9"), hover_color=("#cbd5e1", "#475569"),
                                      command=lambda: self.open_local_path("Captured Images"))
        btn_open_imgs.pack(fill="x", padx=20, pady=8)
        
        btn_open_csv = ctk.CTkButton(card_dir, text="📊 Open Attendance Log File (CSV)", font=ctk.CTkFont("Segoe UI", 12, "normal"), 
                                     height=40, fg_color=("#e2e8f0", "#334155"), text_color=("#0f172a", "#f1f5f9"), hover_color=("#cbd5e1", "#475569"),
                                     command=self.open_database_file)
        btn_open_csv.pack(fill="x", padx=20, pady=(8, 20))
        
        # Column 1: System Actions & Danger Zone
        card_system = ctk.CTkFrame(frame, fg_color=("#ffffff", "#1e293b"), corner_radius=12, border_width=1, border_color=("#e2e8f0", "#334155"))
        card_system.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)
        card_system.grid_columnconfigure(0, weight=1)
        
        lbl_sys_title = ctk.CTkLabel(card_system, text="⚠️ Danger Zone", font=ctk.CTkFont("Segoe UI", 16, "bold"), text_color="#ef4444")
        lbl_sys_title.pack(anchor="w", padx=20, pady=(20, 5))
        lbl_sys_desc = ctk.CTkLabel(card_system, text="Reset application data logs. Action is irreversible.", 
                                     font=ctk.CTkFont("Segoe UI", 12), text_color=("#64748b", "#94a3b8"))
        lbl_sys_desc.pack(anchor="w", padx=20, pady=(0, 20))
        
        btn_reset_csv = ctk.CTkButton(card_system, text="Reset Attendance Log Database", font=ctk.CTkFont("Segoe UI", 12, "bold"), 
                                      height=45, fg_color="#ef4444", hover_color="#dc2626",
                                      command=self.reset_attendance_db)
        btn_reset_csv.pack(fill="x", padx=20, pady=10)
        
        btn_reset_qrs = ctk.CTkButton(card_system, text="Delete All Generated QRs", font=ctk.CTkFont("Segoe UI", 12, "bold"), 
                                      height=45, fg_color="#ef4444", hover_color="#dc2626",
                                      command=self.delete_all_qrs)
        btn_reset_qrs.pack(fill="x", padx=20, pady=(10, 20))
        
        return frame
        
    def open_local_path(self, folder_name):
        try:
            if not os.path.exists(folder_name):
                os.makedirs(folder_name)
            os.startfile(folder_name)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open directory: {str(e)}")
            
    def open_database_file(self):
        try:
            if os.path.exists(data_file):
                os.startfile(data_file)
            else:
                messagebox.showerror("Error", "Log Database does not exist yet. Please record attendance first.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file: {str(e)}")
            
    def reset_attendance_db(self):
        confirm = messagebox.askyesno("Confirm Data Reset", "Are you sure you want to delete all attendance entries?\nThis action cannot be undone.")
        if confirm:
            try:
                with open(data_file, "w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Student ID", "Course Name", "Date", "Total Attended"])
                messagebox.showinfo("Success", "Attendance database reset successfully!")
                self.refresh_dashboard()
            except Exception as e:
                messagebox.showerror("Reset Error", f"Could not clear database: {str(e)}")
                
    def delete_all_qrs(self):
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete all generated Student QR PNG codes?\nThis will clear Student QR folder.")
        if confirm:
            try:
                folder = "Student QR"
                if os.path.exists(folder):
                    count = 0
                    for filename in os.listdir(folder):
                        file_path = os.path.join(folder, filename)
                        if os.path.isfile(file_path) and filename.endswith(".png"):
                            os.remove(file_path)
                            count += 1
                    messagebox.showinfo("Success", f"Successfully deleted {count} QR code files.")
                else:
                    messagebox.showinfo("Info", "Student QR folder does not exist or is empty.")
                self.refresh_dashboard()
            except Exception as e:
                messagebox.showerror("Deletion Error", f"An error occurred while deleting: {str(e)}")


if __name__ == "__main__":
    app = SmartAttendanceApp()
    app.mainloop()