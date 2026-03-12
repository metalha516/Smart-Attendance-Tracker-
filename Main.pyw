import tkinter as tk
import cv2
from pyttsx3 import speak
import os
from datetime import datetime as dt
import keyboard as key
from time import sleep
import tkinter as tk
from tkinter import ttk
import qrcode
import csv

current_dir = os.getcwd()
os.chdir(current_dir)

data_file = "data.csv"

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
    Returns a list of QRResult objects similar to pyzbar.decode().
    """
    qr_detector = cv2.QRCodeDetector()
    results = []

    # Try multi-detection
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
                if row[0] == student_id and row[1] == course_name:
                    unique_dates.add(row[2])
        
        return len(unique_dates)+1
    except Exception as e:
        print(e)

def is_duplicate(student_id, course_name, date):
    try:
        if not os.path.exists(data_file):
            return False
        with open(data_file, "r") as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row[0] == student_id and row[1] == course_name and row[2] == date:
                    return True
        return False
    except Exception as e:
        print(e)

def data_entry(student_id, course_name, current_date):
    try:    
        total = count_attendance(student_id, course_name)
        if not is_duplicate(student_id, course_name, current_date):
            with open(data_file, "a", newline="") as file:
                writer = csv.writer(file)
                writer.writerow([student_id, course_name, current_date, total])
            print(f"Attendance Recorded for {course_name}! total days attended : {total} ")
        else:
            speak("Duplicate Entry")
            print(f"Duplicate Entry - attendence for {course_name} already marked")
    except Exception as e:
        print(e)
    
def capture(frame, file_name):
    try:
        folder_name = "Captured Images"
        if  os.path.exists(folder_name):
            img_path = os.path.join(folder_name, file_name)
            cv2.imwrite(img_path, frame)
        else:
            os.makedirs(folder_name)
            img_path = os.path.join(folder_name, file_name)
            cv2.imwrite(img_path, frame)
    except Exception as e:
        print(e)

def QR_detector(frame, course_name):
    try:
        qr = custom_decode(frame)
        date = ""
        with open(data_file, "a") as f:
            if qr:
                print("Qr Detected")
                for barcode in qr:
                    my_id = barcode.data.decode('utf-8')
                    print(my_id)
                    date = dt.now().strftime('%d_%m_%Y')
                    name = f"{date}_{my_id}.jpg"
                    break
                capture(frame, name)
                data_entry(my_id, course_name, date)
                sleep(2)
            else:
                print("OR not detected")
    except Exception as e:
        print(e)

def main(cn):
    try:
        Course_Name = cn
        cam = cv2.VideoCapture(0)
        if  cam.isOpened():
            while True:
                _,frame = cam.read()
                QR_detector(frame, Course_Name)
                cv2.imshow("Camera", frame)
                cv2.waitKey(1)
            
                if key.is_pressed('esc'):
                    break
            cv2.destroyAllWindows()
        else: 
            print("Camera is not opening....")
            exit()
    except Exception as e:
        print(e)

def registry_qr(entry):
    try:
        set_id = entry.strip()
        
        if not set_id:  # Check for empty input
            print("Error: Student ID cannot be empty!")
            return

        img = qrcode.make(set_id)  # Generate QR code

        folder_name = "Student QR"
        file_name = f"{set_id}.png"
        
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        QR_link = os.path.join(folder_name, file_name)
        img.save(QR_link) 
    except Exception as e:
        print(e)

# PROFESSIONAL GUI DESIGN

# Custom Entry Widget with Modern Design
class ModernEntry(tk.Frame):
    def __init__(self, parent, placeholder="", width=300, *args, **kwargs):
        super().__init__(parent, bg="#f8f9fa", relief="flat", bd=0, *args, **kwargs)
        
        # Entry field
        self.entry = tk.Entry(self, 
                             font=("Segoe UI", 14),
                             bg="white", 
                             fg="#2c3e50",
                             relief="flat",
                             bd=0,
                             width=int(width/10),
                             insertbackground="#3498db")
        self.entry.pack(pady=12, padx=20, fill="x")
        
        # Modern border
        self.configure(highlightbackground="#e1e8ed", highlightthickness=2)
        
        # Bind focus events for border color change
        self.entry.bind("<FocusIn>", self.on_focus_in)
        self.entry.bind("<FocusOut>", self.on_focus_out)
        
    def on_focus_in(self, event):
        self.configure(highlightbackground="#3498db")
    
    def on_focus_out(self, event):
        self.configure(highlightbackground="#e1e8ed")
        
    def get(self):
        return self.entry.get()
    
    def delete(self, first, last):
        self.entry.delete(first, last)
    
    def focus(self):
        self.entry.focus()

def create_modern_button(parent, text, command, bg_color="#3498db", hover_color="#2980b9", text_color="white"):
    button = tk.Button(parent,
                      text=text,
                      command=command,
                      font=("Segoe UI", 12, "bold"),
                      bg=bg_color,
                      fg=text_color,
                      relief="flat",
                      bd=0,
                      padx=40,
                      pady=12,
                      cursor="hand2",
                      activebackground=hover_color,
                      activeforeground="white")
    
    # Hover effects
    def on_enter(e):
        button.config(bg=hover_color)
    
    def on_leave(e):
        button.config(bg=bg_color)
    
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)
    
    return button

def on_register():
    # Hide main menu
    main_menu_frame.pack_forget()
    
    # Show refresh button at exact position (20, 90)
    refresh_button.place(x=20, y=90)
    
    # Show input form
    input_frame.pack(expand=True, fill="both")
    label_var.set("Enter Student ID")
    
    # Show register button and hide attendance button
    input_register_button.pack(pady=(0, 0))
    input_attendance_button.pack_forget()
    
    modern_entry.focus()

def on_check_attendance():
    # Hide main menu
    main_menu_frame.pack_forget()
    
    # Show refresh button at exact position (20, 90)
    refresh_button.place(x=20, y=90)
    
    # Show input form
    input_frame.pack(expand=True, fill="both")
    label_var.set("Enter Course Name")
    
    # Show attendance button and hide register button
    input_attendance_button.pack(pady=(0, 0))
    input_register_button.pack_forget()
    
    modern_entry.focus()

def on_submit():
    input_value = modern_entry.get().strip()
    if not input_value:
        status_label.config(text="⚠️ Input cannot be empty!", fg="#e74c3c")
        return
    
    status_label.config(text="Processing...", fg="#f39c12")
    root.update()
    
    only_digit = input_value.isdigit()
    if only_digit:
        try:
            registry_qr(input_value)
            status_label.config(text="✅ QR Code generated successfully!", fg="#27ae60")
        except Exception as e:
            print(e)
            status_label.config(text="❌ Error generating QR code!", fg="#e74c3c")
    else:
        status_label.config(text="📷 Starting camera...", fg="#3498db")
        root.update()
        main(input_value)

def on_refresh():
    # Hide input form and refresh button
    input_frame.pack_forget()
    refresh_button.place_forget()
    
    # Hide input form buttons
    input_register_button.pack_forget()
    input_attendance_button.pack_forget()
    
    # Clear entry and status
    modern_entry.delete(0, tk.END)
    status_label.config(text="", fg="#2c3e50")
    
    # Show main menu with both buttons
    main_menu_frame.pack(expand=True, fill="both")

# Create main window with modern design
root = tk.Tk()
root.geometry("700x600")
root.title("Attendance Management System")
root.configure(bg="#f8f9fa")
root.resizable(False, False)

# Handle window close button (X)
def on_closing():
    try:
        cv2.destroyAllWindows()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

# Handle home key to go to home page
def on_key_press(event):
    if event.keysym == 'Home':
        on_refresh()

root.bind('<Key>', on_key_press)
root.focus_set()

# Apply modern window style
try:
    root.tk.call('source', 'azure.tcl')
    root.tk.call('set_theme', 'light')
except:
    pass  # Theme not available, continue with default

# Header Section (80px as specified)
header_frame = tk.Frame(root, bg="#2c3e50", height=80)
header_frame.pack(fill="x")
header_frame.pack_propagate(False)

header_title = tk.Label(header_frame, 
                       text="🎓 Attendance Management System", 
                       font=("Segoe UI", 20, "bold"),
                       bg="#2c3e50", 
                       fg="white")
header_title.pack(expand=True)

# Refresh button (initially hidden, positioned at (20, 90) when shown)
refresh_button = tk.Button(root, 
                          text="⟲ Refresh",
                          command=on_refresh,
                          font=("Segoe UI", 10, "bold"),
                          bg="#95a5a6",
                          fg="white",
                          relief="flat",
                          bd=0,
                          padx=15,
                          pady=8,
                          cursor="hand2",
                          activebackground="#7f8c8d")

# Main Menu Frame
main_menu_frame = tk.Frame(root, bg="#f8f9fa")
main_menu_frame.pack(expand=True, fill="both")

# Welcome section
welcome_frame = tk.Frame(main_menu_frame, bg="#f8f9fa")
welcome_frame.pack(expand=True)

welcome_label = tk.Label(welcome_frame, 
                        text="Welcome to Smart Attendance System", 
                        font=("Segoe UI", 16, "bold"),
                        bg="#f8f9fa", 
                        fg="#2c3e50")
welcome_label.pack(pady=(50, 10))

subtitle_label = tk.Label(welcome_frame, 
                         text="Choose an option to get started", 
                         font=("Segoe UI", 12),
                         bg="#f8f9fa", 
                         fg="#7f8c8d")
subtitle_label.pack(pady=(0, 40))

# Modern buttons for main menu
register_button = create_modern_button(welcome_frame, 
                                      "👤 Register Student", 
                                      on_register,
                                      "#27ae60", "#229954")

check_attendance_button = create_modern_button(welcome_frame, 
                                              "📋 Take Attendance", 
                                              on_check_attendance,
                                              "#3498db", "#2980b9")

register_button.pack(pady=15)
check_attendance_button.pack(pady=15)

# Input Form Frame (initially hidden)
input_frame = tk.Frame(root, bg="#f8f9fa")

# Input form content with proper spacing
input_content_frame = tk.Frame(input_frame, bg="#f8f9fa")
input_content_frame.pack(expand=True, fill="both")

# Top spacer to center content properly
top_spacer = tk.Frame(input_content_frame, bg="#f8f9fa", height=80)
top_spacer.pack(fill="x")

# Input label with proper spacing from top
label_var = tk.StringVar()
input_label = tk.Label(input_content_frame,
                      textvariable=label_var,
                      font=("Segoe UI", 16, "bold"),
                      bg="#f8f9fa",
                      fg="#2c3e50")
input_label.pack(pady=(0, 20))

# Modern entry field centered
modern_entry = ModernEntry(input_content_frame, width=400)
modern_entry.pack(pady=(0, 20))

# Button container for proper positioning
button_container = tk.Frame(input_content_frame, bg="#f8f9fa")
button_container.pack(pady=(0, 20))

# Create buttons for input form (initially hidden)
input_register_button = create_modern_button(button_container, 
                                           "👤 Register Student", 
                                           on_submit,
                                           "#27ae60", "#229954")

input_attendance_button = create_modern_button(button_container, 
                                             "📋 Take Attendance", 
                                             on_submit,
                                             "#3498db", "#2980b9")

# Spacer to push status to bottom
middle_spacer = tk.Frame(input_content_frame, bg="#f8f9fa")
middle_spacer.pack(expand=True, fill="both")

# Status label at bottom as specified in layout
status_label = tk.Label(input_content_frame,
                       text="",
                       font=("Segoe UI", 11),
                       bg="#f8f9fa",
                       fg="#2c3e50")
status_label.pack(side="bottom", pady=(0, 40))

# Footer
footer_frame = tk.Frame(root, bg="#ecf0f1", height=40)
footer_frame.pack(fill="x", side="bottom")
footer_frame.pack_propagate(False)

footer_label = tk.Label(footer_frame, 
                       text="© 2024 Smart Attendance System - Powered by AI", 
                       font=("Segoe UI", 9),
                       bg="#ecf0f1", 
                       fg="#7f8c8d")
footer_label.pack(expand=True)

# Run the main loop
root.mainloop()