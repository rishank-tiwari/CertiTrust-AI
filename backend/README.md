# CertiTrust AI - AI Backend Development Environment Guide

## 1. Production Virtual Environment Setup Guide

Follow these steps to create a clean, production-grade Python 3.11 virtual environment for **CertiTrust AI**:

### Step 1: Create Virtual Environment
```bash
# Windows (PowerShell / CMD)
python -m venv venv

# Linux / macOS
python3 -m venv venv
```

### Step 2: Activate Virtual Environment
```bash
# Windows PowerShell
.\venv\Scripts\Activate.ps1

# Windows CMD
.\venv\Scripts\activate.bat

# Linux / macOS
source venv/bin/activate
```

### Step 3: Upgrade Package Installers
```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 4: Install Project Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Verify AI Environment & Startup Banner
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 2. Environment Variables (`.env.example`)

The backend uses `python-dotenv` to load environment configuration from `.env`:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `MONGODB_URI` | `mongodb://localhost:27017/certitrust_ai` | MongoDB connection URI for persistent database |
| `JWT_SECRET` | `certitrust_ai_jwt_super_secret...` | Secret key for JWT authentication tokens |
| `UPLOAD_FOLDER` | `uploads` | Directory for storing uploaded certificates |
| `MAX_FILE_SIZE` | `26214400` (25 MB) | Maximum permitted file upload size in bytes |
| `API_VERSION` | `v1` | Version prefix for REST API endpoints (`/api/v1`) |
| `HOST` | `0.0.0.0` | Host IP address binding |
| `PORT` | `8000` | Server port binding |

---

## 3. Environment & Startup Validation Architecture

On server startup, FastAPI executes `lifespan` validation checks:
1. **Environment Variables Loaded Check**: Validates `MONGODB_URI`, `JWT_SECRET`, `UPLOAD_FOLDER`, `MAX_FILE_SIZE`, and `API_VERSION`.
2. **Directory Integrity Check**: Ensures `uploads/`, `templates/`, and `sample_documents/` exist (auto-creates if missing).
3. **Startup Banner Display**:
   ```
   ==================================
   CertiTrust AI Backend Started
   FastAPI Ready
   AI Modules Ready
   Version: v1
   ==================================
   ```

---

## 4. Installed AI Library Stack (`requirements.txt`)

- **Backend**: `fastapi`, `uvicorn`, `python-multipart`, `requests`
- **OCR**: `paddleocr`, `paddlepaddle`
- **Computer Vision**: `opencv-python`, `Pillow`, `imutils`
- **Machine Learning**: `torch`, `torchvision`
- **NLP**: `spacy`, `transformers`
- **Data & Utilities**: `numpy`, `pandas`, `scikit-learn`
- **PDF Processing**: `pymupdf`, `pdf2image`, `pypdf`
- **Environment & Validation**: `python-dotenv`, `pydantic`
- **Database**: `pymongo`
- **Auth & Security**: `python-jose`, `passlib[bcrypt]`
- **Logging**: `loguru`
