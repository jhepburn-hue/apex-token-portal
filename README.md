# Apex Token Portal

An automated configuration management portal and asset compilation pipeline built with Flask. The portal acts as an orchestration layer that interfaces with Forge pipelines, uses artifacts in Google Cloud Storage (GCS), and registers unique tokens inside PocketBase for readers.

---

## Core Features & Architecture

* **Multi-Build Pipeline Integration:** Bridges partial configurations, configuration profiles, and firmware updates with automated builds on Forge.
* **PocketBase Cache Layer:** Bypasses compilation and serves cached tokens if an active token is found inside PocketBase.
* **Dynamic Content Syncing:** Uploads generated partial configurations to GCS while maintaining a background status worker (background_pipeline_worker) tracking compile lifecycles.
* **Integrated API Clients:** Uses native Python clients to handle authentication, CSV uploads, pipeline builds, and token generation via REST APIs.
* **TCI & TRA Mode Generation:** Constructs customized terminal configuration INI partials combining Terminal IDs with a TRA Mode state toggle (`terminal_info = 0x83` for ON, `0x00` for OFF).
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
│   ├── ini_builder.py                # Constructs partial INI files from feature web forms and TCI/TRA inputs
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
python3 -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install the application packages
pip install -r requirements.txt
```

## Usage & Workflow

Launch the sever:
```bash
python3 app.py
```

Open your web browser and navigate to **http://127.0.0.1:5000** to access the dashboard.
