# Apex Token Portal

An automated configuration management portal and asset compilation pipeline built with Flask. The portal acts as an orchestration layer that interfaces with Forge pipelines, uses artifacts in Google Cloud Storage (GCS), and registers unique tokens inside PocketBase for readers.

---

## Core Features & Architecture

* **Unified Full-Profile Pipeline:** Merges firmware and profiles configuration updates into a single engine workflow with optional DCK injection.
* **Batch Request Processing:** Supports the simultaneous entry and processing of multiple configurations within a single submission block.
* **Consolidated Cache-Checking Layer:** Bypasses compile lifecycles and immediately serves active tokens if an identical record exists within PocketBase.
* **Integrated Asynchronous Syncing:** Dispatches generated profile changes directly to GCS while executing a background status routine (`background_pipeline_worker`) to monitor long-running compile lifetimes.
* **Modular Partial Feature Overrides:** Groups hardware adjustment controls—including standard settings flags (Anti-Passback, OSDP, BLE) and Terminal Configuration data (TCI Address mappings + TRA Mode hex bytes)—under a single partial INI builder environment.
* **Unified Visual Presentation:** Features a web terminal (`loading.html` and dynamic `/status/<filename_stem>` polling) to seamless handle active asynchronous lookups and new compilations.

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
├── app.py              # Primary Flask web application and background worker routing logic
├── forge_client.py     # API Client managing remote Forge pipeline build signals
├── pocketbase_client.py# API Client validating active tokens and tracking cache records
├── default.ini         # Global default baseline hardware settings layer
├── requirements.txt    # Application system package dependency manifest
├── apex_configs/       # Local repository directory housing hardware mapping files (.csv)
│   ├── CDCC1.csv
│   ├── CLTK3.csv
│   └── ...
├── utils/
│   └── ini_builder.py  # Generates custom parameter payloads from standard form toggles and TCI/TRA blocks
├── templates/          # Jinja2 presentation layout view directories
└── static/             # Layout styling definitions and static stylesheets
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
