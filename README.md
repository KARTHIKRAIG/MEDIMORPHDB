
# MEDIMORPH - Prescription Digitization & Medication Reminder System (MongoDB)

A comprehensive AI-powered application that digitizes prescriptions using OCR and provides intelligent medication reminders with user authentication and real-time features.

## 🚀 Features

### 🔐 User Authentication & Security
- **User Registration & Login**: Secure user accounts with password hashing
- **Session Management**: Flask-Login integration for secure sessions
- **User Profiles**: Personal information management
- **Multi-user Support**: Each user has their own medication data

### 📸 Prescription Digitization
- **OCR Processing**: Extract text from prescription images using Tesseract OCR
- **AI-Powered Extraction**: Use machine learning to identify medications, dosages, and frequencies
- **Multiple Recognition Methods**: Combines rule-based, pattern-based, and NER-based extraction
- **Image Preprocessing**: Advanced image processing for better OCR accuracy

### 💊 Medication Management
- **Smart Parsing**: Automatically extract medication names, dosages, frequencies, and durations
- **Database Storage**: MongoDB (via MongoEngine)
- **Edit & Delete**: Manage your medication list with ease
- **Medication History**: Track when medications were taken

### ⏰ Intelligent Reminders
- **Automatic Scheduling**: Set up reminders based on prescription frequency
- **Multiple Frequencies**: Support for daily, twice daily, three times daily, etc.
- **Real-time Notifications**: Get reminded when it's time to take medication
- **Dose Tracking**: Mark medications as taken and track compliance

### 🔄 Real-time Features
- **WebSocket Integration**: Live updates using Flask-SocketIO
- **Instant Notifications**: Real-time medication reminders
- **Live Updates**: Medication changes appear instantly across all connected clients
- **Background Processing**: Continuous reminder checking in background threads

### 🎨 Modern Web Interface
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Intuitive UI**: Clean, modern interface with easy navigation
- **User Dashboard**: Personalized medication management interface

## 🛠️ Technology Stack

- **Backend**: Python Flask, Flask-Login, Flask-SocketIO
- **Database**: MongoDB (MongoEngine ODM)
- **Authentication**: Flask-Login with password hashing
- **Real-time**: Socket.IO
- **OCR**: Tesseract with OpenCV preprocessing
- **AI/ML**: Scikit-learn patterns (no heavy models required)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5

## 📋 Prerequisites

### System Requirements
- Python 3.8 or higher
- Windows 10/11 (for Tesseract installation)
- At least 4GB RAM
- 2GB free disk space

### Required Software
1. **Python**: `https://python.org`
2. **Tesseract OCR**: `https://github.com/UB-Mannheim/tesseract/wiki`
3. **MongoDB Community Server**: `https://www.mongodb.com/try/download/community`
   - Ensure MongoDB service is running on `mongodb://localhost:27017/`
4. (Optional) **Git**: for cloning

## 🚀 Installation

### 1) Get the code
```bash
# If copied as a folder, just place it on the new system
# If cloning:
git clone <repository-url>
cd medimorph
```

### 2) Install Tesseract OCR (Windows)
- Install to default: `C:\Program Files\Tesseract-OCR\`

### 3) Create and activate virtual environment
```bash
python -m venv .venv
.\.venv\Scripts\activate  # PowerShell/Command Prompt
```

### 4) Install dependencies
```bash
pip install -r requirements.txt
```

### 5) Start MongoDB (if not already running)
- Windows Services: start the "MongoDB" service
- Or Docker: `docker run -d --name mongo -p 27017:27017 mongo`

### 6) Run the app (MongoDB version)
```bash
python app_mongodb.py
# or double-click start.bat
```
The app runs at `http://127.0.0.1:5000`.

## 📁 Project Structure

```
medimorph/
├── app_mongodb.py         # Main Flask application (MongoDB)
├── mongodb_config.py      # MongoEngine models and DB setup
├── prescription_ocr.py    # OCR processing module
├── ai_processor.py        # AI/logic for medication extraction
├── medication_reminder.py # (legacy helper, Mongo app has own reminder)
├── requirements.txt       # Python dependencies
├── start.bat              # Windows helper script to run the app
├── README.md              # This file
└── templates/             # Frontend pages (unchanged)
```

## 🔧 Configuration

- MongoDB defaults are set in `mongodb_config.py`:
  - DB: `medimorph_db`
  - URI: `mongodb://localhost:27017/`
- Adjust as needed.

## 🐛 Troubleshooting

- `ImportError: cannot import name 'ObjectId' from 'bson'`:
  - Remove PyPI `bson` package and ensure `pymongo` is installed.
- Tesseract errors: verify install path in `prescription_ocr.py` matches your system.

---

Made with ❤️ for better healthcare management
