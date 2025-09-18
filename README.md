# 🎓 Smart Attendance Tracker

Smart QR Code-Based Attendance Management System with Modern GUI - Track student attendance using computer vision, QR codes, and automated data management

![Python](https://img.shields.io/badge/python-v3.7+-blue.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.x-green.svg)
![GUI](https://img.shields.io/badge/GUI-Tkinter-orange.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

- **📱 QR Code Generation**: Generate unique QR codes for student registration
- **🔍 Real-time QR Detection**: Use computer vision to detect and decode QR codes via webcam
- **📊 Attendance Tracking**: Automatically record attendance with date stamps
- **🚫 Duplicate Prevention**: Prevents multiple attendance entries for the same student on the same day
- **💾 Data Persistence**: Stores attendance data in CSV format for easy access and analysis
- **🎨 Modern GUI**: Clean, professional user interface with hover effects and modern styling
- **🔊 Voice Feedback**: Audio confirmation for successful attendance recording
- **📸 Image Capture**: Automatically captures and saves images when QR codes are detected

## 🚀 Quick Start

### Prerequisites
- Webcam

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Smart-Attendance-Tracker.git
   cd Smart-Attendance-Tracker
   ```
2. **Run the application**
   ```bash
   Main.exe.
   ```

## 📖 How to Use

### 1. 👤 Student Registration

1. Launch the application
2. Click **"👤 Register Student"**
3. Enter the student ID (numbers only)
4. Click **"👤 Register Student"** to generate a QR code
5. The QR code will be saved in the `Student QR` folder as a PNG file

### 2. 📋 Taking Attendance

1. From the main menu, click **"📋 Take Attendance"**
2. Enter the course name
3. Click **"📋 Take Attendance"** to start the camera
4. Students scan their QR codes in front of the camera
5. The system will:
   - Detect and decode the QR code
   - Capture an image with timestamp
   - Record attendance in the CSV file
   - Provide voice confirmation
   - Prevent duplicate entries for the same day

### 3. 🧭 Navigation

- **Refresh Button (⟲)**: Return to the main menu from any screen
- **Home Key**: Press to return to the homepage/main menu from anywhere
- **ESC Key**: Press to exit the application completely
- **X Button**: Close the application

## 📁 File Structure

```
Project Directory/
│
├── attendance_system.py          # Main application file
├── data.csv                      # Attendance records (auto-created)
├── Student QR/                   # Generated QR codes folder
│   ├── [StudentID].png
│   └── ...
└── Captured Images/              # Attendance photos folder
    ├── [Date]_[StudentID].jpg
    └── ...
```

## 📊 Data Format

The attendance data is stored in `data.csv` with the following columns:

| Column | Description |
|--------|-------------|
| Student ID | Unique identifier for the student |
| Course Name | Name of the course/class |
| Date | Date of attendance (DD_MM_YYYY format) |
| Total Attended | Running count of attendance days |

## ⚙️ Technical Details

### 🔍 QR Code Detection
- Uses OpenCV's `QRCodeDetector` for reliable QR code detection
- Supports both single and multiple QR code detection
- Custom implementation that mimics pyzbar functionality

### 💾 Data Management
- CSV-based storage for simplicity and portability
- Automatic duplicate detection based on Student ID, Course, and Date
- Running attendance counter for each student per course

### 🎨 User Interface
- Built with Tkinter and custom styling
- Modern design with hover effects and professional appearance
- Responsive layout with proper spacing and visual hierarchy

## 🐛 Troubleshooting

### Common Issues

**📷 Camera not opening:**
- Ensure your webcam is properly connected
- Check if other applications are using the camera
- Try changing the camera index from `0` to `1` in `cv2.VideoCapture(0)`

**🔍 QR codes not detected:**
- Ensure good lighting conditions
- Hold the QR code steady in front of the camera
- Make sure the QR code is not too small or too large in the frame

**🔒 Permission errors:**
- Make sure the application has write permissions in its directory
- Run as administrator if necessary (Windows)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


⭐ **If you found this project helpful, please give it a star!** ⭐
