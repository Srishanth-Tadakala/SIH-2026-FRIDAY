# Local Development Setup Guide

This guide walks you through setting up a complete F.R.I.D.A.Y. development environment from scratch on Windows, Linux, or macOS.

---

## 1. System Prerequisites

Before starting, ensure you have the following installed:
- **Python**: Version 3.11, 3.12, or 3.14 (Python 3.12+ recommended)
- **Node.js**: Version 20 LTS or 22 LTS
- **npm**: Version 10+ (bundled with Node.js)
- **Git**
- Optional: **Docker** & **Docker Compose** (for containerized execution)
- Optional: **MongoDB** v6.0+ (if running without the automated embedded fallback)

---

## 2. Step-by-Step Installation

### Step 2.1: Clone Repository
```bash
git clone https://github.com/Srishanth-Tadakala/SIH-2026-FRIDAY.git
cd SIH-2026-FRIDAY
```

### Step 2.2: Configure Environment
Copy the documented configuration template to create your local `.env`:
```bash
# Windows PowerShell / CMD
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
*Note: F.R.I.D.A.Y. runs out of the box in `development` mode without editing `.env`. If you have a Groq API key or MongoDB Atlas URI, you can add them to `.env`.*

### Step 2.3: Install Python Backend Dependencies
We recommend using a Python virtual environment:
```bash
# Create and activate virtual environment
python -m venv .venv

# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Windows CMD:
.venv\Scripts\activate.bat
# Linux / macOS:
source .venv/bin/activate

# Install required packages
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.4: Install Frontend Dependencies
```bash
cd frontend
npm ci
cd ..
```

---

## 3. Running the Stack Locally

You can run F.R.I.D.A.Y. in two modes:

### Mode A: Unified Production/Testing Mode (Recommended)
Build the frontend once, then launch the FastAPI server which serves both the API and the compiled React dashboard on port 8000:
```bash
# 1. Build frontend
cd frontend
npm run build
cd ..

# 2. Launch FastAPI platform
python run_server.py
```
Open your browser at:
- **Polar Command Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **System Health Probe**: [http://127.0.0.1:8000/api/health](http://127.0.0.1:8000/api/health)
- **Standalone Cockpit UI**: [http://127.0.0.1:8000/legacy-ui](http://127.0.0.1:8000/legacy-ui)

### Mode B: Dual Development Server Mode (with Hot Reloading)
For active frontend development with instant HMR:
```bash
# Terminal 1: Launch Backend API Server
python run_server.py

# Terminal 2: Launch Vite Dev Server
cd frontend
npm run dev
```
Open the Vite development URL: [http://localhost:5173/](http://localhost:5173/)
