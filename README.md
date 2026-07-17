# Apex Token Portal

An automated configuration management portal and asset compilation pipeline built with Flask. The portal acts as an orchestration layer that interfaces with Forge pipelines, uses artifacts in Google Cloud Storage (GCS), and registers unique tokens inside PocketBase for readers.

---

## Core Features & Architecture

* **Multi-Build Pipeline Integration:** Bridges partial configurations, configuration profiles, and firmware updates with automated builds on Forge.
* **PocketBase Cache Layer:** Bypasses compilation and serves cached tokens if an active token is found inside PocketBase.
* **Dynamic Content Syncing:** Uploads generated partial configurations to GCS while maintaining a background status worker (background_pipeline_worker) tracking compile lifecycles.
* **Integrated API Clients:** Uses native Python clients to handle authentication, CSV uploads, pipeline builds, and token generation via REST APIs.
* **Unified Visual Presentation:** Features an interface (loading.html and polling /status/<filename_stem>) that handles newly compiled tokens and cached lookups.

---

## Prerequisites

To run this application locally, you will need:
* **Python 3.10+** (Python 3.14 compatible)
* Access to a **PocketBase** instance (with admin credentials and target collection configured)
* Access to the **Forge** pipeline endpoint and valid GCP/IAP authentication cookies
* A Google Cloud Platform project with access to the target Google Cloud Storage bucket (wavelynx_apex_config)

---

## Project Structure

```bash
apex-token-portal/
├── app.py                            # Primary Flask web application and background worker logic
├── forge_client.py                   # API Client for Forge config imports and build triggers
├── pocketbase_client.py              # API Client for PocketBase caching and token registration
├── default.ini                       # Global default hardware state baseline
├── application_default_credentials.json # GCP Service Account credentials
├── apex_configs/                     # Local repository of configuration profile CSVs
│   ├── CDCC1.csv
│   ├── CLTK3.csv
│   └── ...
├── utils/
│   ├── ini_builder.py                # Constructs partial INI files from feature web forms
├── templates/                        # Jinja2 HTML templates
└── static/                           # CSS stylesheets and layout styling
```

---

## Local Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/jhepburn-hue/apex-token-portal.git
cd apex-token-portal
```

### 2. Install Dependencies
```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the application packages
pip install -r requirements.txt
```

### 3. Configure Credentials & Environment Variables
The application looks for application_default_credentials.json in the project root for Google Cloud Storage authentication. Additionally, sensitive credentials can be customized via environment variables prior to launching the application.

Run the following commands in your terminal (replace placeholders with actual values if overriding default settings):

**On macOS / Linux:**
```bash
export SECRET_KEY="your-session-cookie-encryption-key"
export PB_BASE_URL="https://unf.wavelynxtech.com/api"
export PB_COLLECTION_ID="your_collection_id"
export PB_ADMIN_TOKEN="your_pocketbase_admin_auth_token_string"
export GOOGLE_CLOUD_PROJECT="erebus-257721"
```

**On Windows (Command Prompt):**
```bash
set SECRET_KEY="your-session-cookie-encryption-key"
set PB_BASE_URL="https://unf.wavelynxtech.com/api"
set PB_COLLECTION_ID="your_collection_id"
set PB_ADMIN_TOKEN="your_pocketbase_admin_auth_token_string"
set GOOGLE_CLOUD_PROJECT="erebus-257721"
```

**On Windows (PowerShell):**
```bash
$env:SECRET_KEY="your-session-cookie-encryption-key"
$env:PB_BASE_URL="https://unf.wavelynxtech.com/api"
$env:PB_COLLECTION_ID="your_collection_id"
$env:PB_ADMIN_TOKEN="your_pocketbase_admin_auth_token_string"
$env:GOOGLE_CLOUD_PROJECT="erebus-257721"
```

## Usage & Workflow

Launch the sever:
```bash
python3 app.py
```

Open your web browser and navigate to **http://127.0.0.1:5000** to access the dashboard.
