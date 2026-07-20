import os
import re
import time
import threading
import traceback
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from google.cloud import storage

from utils.ini_builder import build_partial_ini, build_tra_tci, TERMINAL_INFO_TRA_ON, TERMINAL_INFO_TRA_OFF
from forge_client import ForgeClient
from pocketbase_client import PocketBaseClient

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "apex-portal-dev-key-change-me")

BASE_DIR = Path(__file__).parent
GENERATED_DIR = Path("/tmp/generated")
GENERATED_DIR.mkdir(exist_ok=True)

BUCKET_NAME = "wavelynx_apex_config"
USER_EMAIL = "jhepburn@wavelynx.com"
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "erebus-257721")

KEY_FILE_NAME = "application_default_credentials.json" 
KEY_PATH = BASE_DIR / KEY_FILE_NAME

if KEY_PATH.exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(KEY_PATH)
    print(f"[Auth] Loaded GCP Service Account credentials from: {KEY_PATH.name}")
else:
    print(f"[Auth Warning] {KEY_FILE_NAME} not found in project root. Falling back to default credentials.")

os.environ["FORGE_IAP_CLIENT_ID"] = "876522335360-b4adgb4vtk2bgg6d1ddgcejv86pr6mrn.apps.googleusercontent.com"

# Initialize API Clients
forge_client = ForgeClient()
pb_client = PocketBaseClient()

JOBS = {}

FIRMWARE_IDS = {
    "v5.4.1": "5480",
    "v5.4.6": "75898",
    "v5.4.7": "148301"
}


def to_slug(s: str) -> str:
    s = (s or "").strip().lower()
    return re.sub(r"[^a-z0-9\-\.]", "", re.sub(r"[\s_]+", "-", s))


def upload_to_gcs(file_path: Path, update_type: str, version_dir: str) -> str:
    """Uploads temporary build assets (such as partial INI files) to GCS."""
    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.bucket(BUCKET_NAME)
    
    if update_type in ["feature_update", "tra_tci"]:
        gcs_destination_path = f"forge/{USER_EMAIL}/{version_dir}/partials/{file_path.name}"
    else:
        gcs_destination_path = f"forge/{USER_EMAIL}/{version_dir}/{file_path.name}"

    blob = bucket.blob(gcs_destination_path)
    blob.upload_from_filename(str(file_path))
    print(f"[GCS Upload] Successfully uploaded {file_path.name} to gs://{BUCKET_NAME}/{gcs_destination_path}")
    return gcs_destination_path


def background_pipeline_worker(version_dir: str, filename_stem: str, update_type: str, search_designator: str = None, add_firmware: bool = False, timeout_seconds: int = 240):
    """
    Monitors GCS for compiled binary/firmware output from Forge, downloads it,
    and registers a new ACTIVE token record in PocketBase.
    """
    search_query = (search_designator or filename_stem.split('-')[0]).lower()
    
    if update_type == "feature_update":
        prefix_path = f"forge/{USER_EMAIL}/{version_dir}/partials/"
    else:
        prefix_path = f"forge/{USER_EMAIL}/{version_dir}/"
        
    # FIX 1: The physical file extension in GCS is always ".bin"
    target_ext = ".bin" 
        
    print(f"[Worker] Monitoring GCS: gs://{BUCKET_NAME}/{prefix_path} for '{search_query}' (Firmware mode: {add_firmware})")
    JOBS[filename_stem]["state"] = "compiling"
    
    start_time = time.time()
    
    while time.time() - start_time < timeout_seconds:
        try:
            storage_client = storage.Client(project=GCP_PROJECT)
            blobs = list(storage_client.list_blobs(BUCKET_NAME, prefix=prefix_path))
            
            matching_blobs = []
            for b in blobs:
                name_lower = b.name.lower()
                # FIX 2: Check for presence of "dck" in name if checked, otherwise ensure it doesn't contain "dck"
                if search_query in name_lower and name_lower.endswith(target_ext):
                    if add_firmware and "dck" in name_lower:
                        matching_blobs.append(b)
                    elif not add_firmware and "dck" not in name_lower:
                        matching_blobs.append(b)
            
            if matching_blobs:
                ready_to_process = True
                for b in matching_blobs:
                    b.reload()
                    if b.size == 0:
                        ready_to_process = False
                
                if ready_to_process:
                    print(f"[Worker] Verified stable artifact batch ({len(matching_blobs)} files).")
                    JOBS[filename_stem]["state"] = "uploading"
                    
                    primary_token_id = None
                    
                    for b in matching_blobs:
                        actual_filename = Path(b.name).stem
                        local_download_path = GENERATED_DIR / f"{actual_filename}{target_ext}"
                        
                        print(f"[Worker] Downloading artifact: {b.name}...")
                        b.download_to_filename(str(local_download_path))
                        
                        fname_lower = actual_filename.lower()
                        stem_lower = filename_stem.lower()
                        query_lower = search_query.lower()

                        is_target_file = False
                        
                        if update_type == "config_update":
                            if add_firmware:
                                # FIX 3: Target the "wall_dck" file specifically out of the stack
                                if "wall_dck" in fname_lower or "wall" in fname_lower:
                                    is_target_file = True
                            else:
                                if (query_lower in fname_lower or stem_lower in fname_lower) and "wall" not in fname_lower and "module" not in fname_lower:
                                    is_target_file = True
                        elif update_type == "feature_update":
                            if (query_lower in fname_lower or stem_lower in fname_lower) and "wall" not in fname_lower and "module" not in fname_lower:
                                is_target_file = True

                        if is_target_file:
                            fw_ver = version_dir.lstrip('v')
                            cfg_name = (search_designator or filename_stem.split('-')[0]).upper()
                            
                            if update_type == "config_update" and add_firmware:
                                token_name = f"{fw_ver} {cfg_name} FIRMWARE"
                            elif update_type == "config_update":
                                token_name = f"{fw_ver} {cfg_name} PROFILE"
                            else:
                                clean_details = filename_stem.replace('_', ' ').title()
                                clean_details = clean_details.replace('Osdp', 'OSDP').replace('Led', 'LED').replace('OSDP Baud Rate', 'Baud Rate')
                                clean_details = clean_details.replace('Tci', 'TCI').replace('Tra Off', 'TRA Off').replace('Tra On', 'TRA On')
                                token_name = f"{fw_ver} {clean_details}"

                            token_id = pb_client.create_token_record(token_name, local_download_path)
                            primary_token_id = token_id
                        else:
                            print(f"[Worker] Skipping non-target artifact: {actual_filename}")
                            
                        local_download_path.unlink(missing_ok=True)
                    
                    if not primary_token_id:
                        raise Exception(f"No matching target artifact found for search query '{search_query}'.")

                    JOBS[filename_stem]["token"] = primary_token_id
                    JOBS[filename_stem]["state"] = "completed"
                    print(f"[Worker] Finished processing batch. Returned Token ID: {primary_token_id}")
                    return
            
        except Exception as e:
            print(f"[Worker Exception] {e}")
            JOBS[filename_stem]["state"] = "failed"
            JOBS[filename_stem]["error"] = str(e)
            return
            
        time.sleep(6)
        
    JOBS[filename_stem]["state"] = "failed"
    JOBS[filename_stem]["error"] = "Asset generation timed out waiting for Forge output."


@app.route('/')
def index():
    config_dir = os.path.join(os.path.dirname(__file__), 'apex_configs')
    
    config_names = []
    if os.path.exists(config_dir):
        config_names = [
            os.path.splitext(f)[0] 
            for f in os.listdir(config_dir) 
            if f.endswith('.csv')
        ]
        config_names.sort()

    return render_template('index.html', config_names=config_names)


@app.route("/process", methods=["POST"])
def process():
    form_data = request.form.to_dict(flat=True)
    update_type = form_data.get("update_type")
    
    # ADJUSTMENT 1: Extract the new checkbox flag state
    add_firmware_active = form_data.get("add_firmware") == "true"
    
    # ADJUSTMENT 2: Clean up version fallback extraction (since option 2 is deprecated)
    if update_type == "feature_update":
        firmware_options = request.form.getlist("current_firmware")
        raw_version = firmware_options[1] if len(firmware_options) > 1 else (firmware_options[0] if firmware_options else "v5.4.1")
    else:
        raw_version = form_data.get("current_firmware_update") or "v5.4.1"
        
    if not raw_version.startswith('v'):
        raw_version = f"v{raw_version}"
    version_dir = to_slug(raw_version)

    try:
        config_designator = None
        fw_ver = version_dir.lstrip('v')
        generated_ini_path = None

        # 1. DERIVE TOKEN NAME & TARGET INI STEM
        if update_type == "config_update":
            config_designator = form_data.get("config_designator_update", "").strip().upper()
            # ADJUSTMENT 3: Modify the token designation name dynamic suffix 
            suffix = "FIRMWARE" if add_firmware_active else "PROFILE"
            token_name = f"{fw_ver} {config_designator} {suffix}"
            target_ini_stem = config_designator
        else:
            default_ini_path = BASE_DIR / "default.ini"
            generated_ini_path = build_partial_ini(default_ini_path, GENERATED_DIR, form_data)
            target_ini_stem = generated_ini_path.stem
            clean_details = target_ini_stem.upper().replace('_', ' ').title().replace('Osdp', 'OSDP').replace('Led', 'LED').replace('OSDP Baud Rate', 'Baud Rate')
            token_name = f"{fw_ver} {clean_details}"

        # 2. CACHE CHECK (PocketBase)
        cached_token = pb_client.check_active_token(token_name)
        if cached_token:
            if generated_ini_path and generated_ini_path.exists():
                generated_ini_path.unlink(missing_ok=True)
            return render_template("token_display.html", token=cached_token, cached=True)

        # 3. API INTERACTIONS WITH FORGE
        selected_build_id = FIRMWARE_IDS.get(raw_version, "5480")

        if update_type == "config_update":
            if not config_designator:
                raise Exception("A valid Configuration Designation identifier string must be provided.")
                
            local_csv_source = BASE_DIR / f"apex_configs/{config_designator}.csv"
            if not local_csv_source.exists():
                raise Exception(f"Configuration profile CSV not found locally: {config_designator}.csv")
                
            print(f"[Portal Backend] Importing CSV via Forge API for {config_designator}...")
            import_resp = forge_client.import_csv_config(local_csv_source, target_version=raw_version)
            if import_resp.status_code not in [200, 201, 303]:
                raise Exception(f"Forge CSV Import Failed ({import_resp.status_code}): {import_resp.text}")

            print(f"[Portal Backend] Triggering apex-config build via Forge API...")
            build_resp = forge_client.trigger_config_build(
                config_name=config_designator,
                version=raw_version,
                firmware_build_id=selected_build_id,
                firmware_source="Release",
                include_partials="0"
            )
            if build_resp.status_code not in [200, 201, 303]:
                raise Exception(f"Forge Build Trigger Failed ({build_resp.status_code}): {build_resp.text}")

        elif update_type in ["feature_update", "tra_tci"]:
            upload_to_gcs(generated_ini_path, update_type, version_dir)
            generated_ini_path.unlink(missing_ok=True)

            print(f"[Portal Backend] Triggering feature update build via Forge API...")
            build_resp = forge_client.trigger_config_build(
                config_name=target_ini_stem,
                version=raw_version,
                firmware_build_id=selected_build_id,
                firmware_source="Release",
                include_partials="1",
                gitlab_ref="DEVOPS-212-partial-config-builds"
            )
            if build_resp.status_code not in [200, 201, 303]:
                raise Exception(f"Forge Feature Build Trigger Failed ({build_resp.status_code}): {build_resp.text}")

        # 4. DISPATCH BACKGROUND MONITORING WORKER
        tracking_key = target_ini_stem.upper()
        JOBS[tracking_key] = {"state": "initializing", "token": None, "error": None}

        # ADJUSTMENT 4: Append the add_firmware_active state boolean to the thread arguments
        t = threading.Thread(
            target=background_pipeline_worker, 
            args=(version_dir, tracking_key, update_type, config_designator, add_firmware_active)
        )
        t.daemon = True
        t.start()

        return render_template(
            "loading.html", 
            version=raw_version, 
            filename_stem=target_ini_stem, 
            update_type=update_type, 
            firmware_build_id=selected_build_id
        )
    
    except Exception as e:
        tb = traceback.format_exc()
        return render_template("error.html", error=str(e), traceback_text=tb), 500


@app.route("/status/<filename_stem>", methods=["GET"])
def job_status(filename_stem):
    job = JOBS.get(filename_stem.upper(), {"state": "unknown", "token": None, "error": None})
    return jsonify(job)


@app.route("/token_display_view", methods=["GET"])
def token_display_view():
    token = request.args.get("token", "")
    is_cached = request.args.get("cached", "false").lower() == "true"
    return render_template("token_display.html", token=token, cached=is_cached)


if __name__ == "__main__":
    app.run(port=5000, debug=True, use_reloader=False)