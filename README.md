# 🚗 SafeRoute Peddapalli

Welcome to **SafeRoute Peddapalli**! 

**Repository:** [https://github.com/saicharan-bhuthkuri/SafeRoute_Peddapalli.git](https://github.com/saicharan-bhuthkuri/SafeRoute_Peddapalli.git)

This is a full-stack web application designed to predict the safety and risk of road travel routes in the Peddapalli region. By leveraging a Machine Learning model (Random Forest), SafeRoute evaluates road safety based on historic accident data, weather conditions, time of day, and road types, providing users with the safest possible routes.


---

## 📂 Detailed File Structure

Here is a comprehensive breakdown of the project folders and what each file does:

```text
SafeRoute_Peddapalli/
│
├── backend/                 # 🐍 Python / FastAPI Backend Services
│   ├── main.py              # The main entry point for the FastAPI server (handles APIs like /get-route)
│   ├── database.py          # Establishes the connection to the SQLite database using SQLAlchemy
│   ├── models.py            # Defines the database tables (e.g., AccidentRecord)
│   ├── routing.py           # Contains the core logic to calculate the safest route between two points
│   ├── data_parser.py       # Helper functions to clean, parse, and encode raw CSV data
│   ├── train_ml.py          # Script that trains the Random Forest ML model using the accident data
│   ├── load_data.py         # Script that reads CSV data and inserts it into the SQLite database
│   ├── requirements.txt     # A list of all the Python packages needed to run the backend
│   ├── saferoute.db         # The local SQLite database file containing all the accident records
│   └── ml_model_data/       # Stores the trained model files (rf_model.joblib, encoders.joblib)
│
├── frontend/                # ⚡ SvelteKit / Vite / TailwindCSS Frontend Application
│   ├── package.json         # Lists all Node.js dependencies and defines scripts like 'npm run dev'
│   ├── svelte.config.js     # Default configuration for the SvelteKit framework
│   ├── vite.config.ts       # Configuration for Vite (the build tool and dev server)
│   ├── tsconfig.json        # Configuration for TypeScript (adds strict typing to JavaScript)
│   ├── src/                 # The main folder containing the UI code (Svelte components, CSS, pages)
│   └── static/              # Where public assets like images, icons, or global CSS live
│
├── database/                # Any supplementary database scripts/tools
├── ml_model/                # Exploratory Jupyter Notebooks or raw ML research
└── shared/                  # Code or configuration files meant to be shared across the project
```

---

## 🛠 Prerequisites (What you need installed)

Before you begin, ensure you have the following software installed on your computer:

1. **Python 3.9 or higher** (Required for the Backend)
   - Download from [python.org](https://www.python.org/downloads/).
   - **Important for Windows Users:** During installation, make sure to check the box that says **"Add Python to PATH"**. If you skip this, terminal commands like `python` or `pip` will not be recognized.
2. **Node.js v18 or higher** (Required for the Frontend)
   - Download from [nodejs.org](https://nodejs.org/). This will also install `npm` (Node Package Manager).

---

## 🚀 Step-by-Step Installation & Setup

You must set up the **Backend** and the **Frontend** separately. 

### Part 1: Setting up the Backend (Python)

You need to open a terminal exactly inside the `backend` folder.

1. **Open your Terminal (or Command Prompt / PowerShell)**
2. **Navigate exactly into the backend directory:**
   ```bash
   cd path/to/SafeRoute_Peddapalli/backend
   ```
   *(Make sure your terminal path ends exactly in `...\SafeRoute_Peddapalli\backend`)*

3. **Create a Virtual Environment (Recommended):**
   This creates an isolated environment so your project dependencies don't clash with other Python projects.
   ```bash
   python -m venv venv
   ```
   *(If `python` isn't recognized, try `py -m venv venv` or `python3 -m venv venv`)*

4. **Activate the Virtual Environment:**
   - **On Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **On Windows (Command Prompt):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **On Mac/Linux:**
     ```bash
     source venv/bin/activate
     ```
   *(Once activated, you should see `(venv)` appear at the beginning of your terminal line).*

5. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```
   *(If you get "pip is not recognized", verify that Python is installed and added to your system PATH, or ensure your virtual environment is properly activated).*

6. **Initialize the Database and ML Model (First time only):**
   If this is your first time running the project, you need to load the accident data and train the machine learning model.
   ```bash
   python load_data.py
   python train_ml.py
   ```

### Part 2: Setting up the Frontend (Node.js/Svelte)

1. **Open a NEW, second terminal window.**
2. **Navigate exactly into the frontend directory:**
   ```bash
   cd path/to/SafeRoute_Peddapalli/frontend
   ```
   *(Make sure your terminal path ends exactly in `...\SafeRoute_Peddapalli\frontend`)*

3. **Install the required Node.js packages:**
   ```bash
   npm install
   ```

---

## 🏃‍♂️ How to Run the Application

To use the app, you need to have **both** the backend and the frontend running at the same time in two different terminal windows.

### 1. Start the Backend API Server
In your first terminal (the one inside the `backend` folder with the `(venv)` activated):
```bash
uvicorn main:app --reload
```
- The backend API will now be listening at: **http://127.0.0.1:8000**
- You can view the automatic Interactive API Documentation at: **http://127.0.0.1:8000/docs**

### 2. Start the Frontend User Interface
In your second terminal (the one inside the `frontend` folder):
```bash
npm run dev
```
- The UI will be available at: **http://localhost:5173** (or whichever port Vite assigns).
- **Control + Click** (or **Cmd + Click**) the link in the terminal to open it in your web browser.

---

## 🚨 Troubleshooting Common Errors

- **`pip` or `python` is not recognized:** You forgot to check "Add Python to PATH" when installing Python. Reinstall Python and make sure that box is checked. Alternatively, use `py -m pip` instead of `pip`.
- **`npm` is not recognized:** You do not have Node.js installed, or you need to restart your terminal after installing it.
- **ModuleNotFoundError in Python:** Ensure you activated your virtual environment (`.\venv\Scripts\activate`) before running `pip install -r requirements.txt`.
- **Frontend can't connect to Backend:** Ensure both terminals are running simultaneously without errors. Also, check that your backend is running on port `:8000` as expected by the frontend.
