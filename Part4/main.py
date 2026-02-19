import json
import os
import subprocess
import threading
import uuid
from typing import Dict
from fastapi import BackgroundTasks, FastAPI, HTTPException
from nuclei_html_report import convert_nuclei_to_html

app = FastAPI(title="Parallel Security Scanner")

# In-memory tracking for scan statuses.
scans_db: Dict[str, dict] = {}

# --- Configuration ---
DEFAULT_TARGET = "http://testphp.vulnweb.com"
DEFAULT_MODEL_TYPE = "ollama"
DEFAULT_MODEL_NAME = "llama3"
INTERNAL_REPORTS_PATH = "/reports"

def get_host_reports_path() -> str:
    """Return a Docker-friendly host path for volume mounts."""
    raw_path = os.getenv("REAL_HOST_PATH", os.getcwd() + "/reports")
    return raw_path

HOST_REPORTS_PATH = get_host_reports_path()

def convert_nuclei_json_to_html(scan_id: str) -> None:
    """
    Convert Nuclei JSON report to HTML using pure Python.
    Reads the JSON file and generates a formatted HTML report.
    """
    try:
        print(f"[nuclei-html-converter] Starting conversion for scan {scan_id}...")
        
        # Build the file paths
        json_file = os.path.join(HOST_REPORTS_PATH, f"nuclei_{scan_id}.json")
        html_file = os.path.join(HOST_REPORTS_PATH, f"nuclei_{scan_id}.html")
        
        # Check if JSON file exists
        if not os.path.exists(json_file):
            print(f"[nuclei-html-converter] JSON file not found: {json_file}")
            return
        
        # Read the JSON file
        with open(json_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Parse JSON lines (Nuclei outputs newline-delimited JSON)
        vulnerabilities = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    vuln = json.loads(line)
                    vulnerabilities.append(vuln)
                except json.JSONDecodeError:
                    continue
        
        # Generate HTML report from vulnerabilities
        html_content = generate_nuclei_html_report(vulnerabilities, scan_id)
        
        # Write HTML file
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"[nuclei-html-converter] HTML report generated successfully: {html_file}")
    
    except Exception as exc:
        print(f"[nuclei-html-converter] Error: {exc}")


def run_tool_thread(tool_name: str, command: list, scan_id: str) -> None:
    """Run a single tool and update its status in the scan database."""
    scans_db[scan_id]["tools"][tool_name] = "in_progress"

    try:
        print(f"[{tool_name}] Preparing to start...")
        # Execute the tool command
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        # Log standard output (truncated to avoid clutter)
        if result.stdout:
            print(f"[{tool_name}] STDOUT: {result.stdout[:500]}...")

        # Log error output for debugging
        if result.stderr:
            print(f"[{tool_name}] STDERR:\n{result.stderr}")

        # Handle tool completion status
        if result.returncode != 0:
            # ZAP returns 2 for warnings; treat that as success.
            if tool_name == "zap" and result.returncode == 2:
                scans_db[scan_id]["tools"][tool_name] = "finished"
            else:
                print(f"!!! Error in {tool_name} (Exit Code {result.returncode}) !!!")
                scans_db[scan_id]["tools"][tool_name] = "failed"
        else:
            print(f"[{tool_name}] Finished successfully.")
            scans_db[scan_id]["tools"][tool_name] = "finished"
            
            # After nuclei completes, convert its JSON output to HTML
            if tool_name == "nuclei":
                print("[nuclei] Triggering HTML report generation...")
                convert_nuclei_to_html("./reports")

    except Exception as exc:
        print(f"Critical Exception in {tool_name}: {exc}")
        scans_db[scan_id]["tools"][tool_name] = "failed"

    # Check if all tools are done and update overall scan status
    update_overall_status(scan_id)


def update_overall_status(scan_id: str) -> None:
    """Aggregate tool statuses into a single scan status."""
    statuses = scans_db[scan_id]["tools"].values()
    if "in_progress" not in statuses:
        if "failed" in list(statuses):
            scans_db[scan_id]["status"] = "finished_with_errors"
        else:
            scans_db[scan_id]["status"] = "completed"


def normalize_model_name(model_name: str) -> str:
    """Ensure Ollama model names include a tag."""
    return model_name if ":" in model_name else f"{model_name}:latest"


def build_tool_commands(target: str, scan_id: str, model_name: str) -> Dict[str, list]:
    """Build the Docker and local commands for each scanner tool."""
    return {
        "nuclei": [
            "docker",
            "run",
            "--rm",
            "--user",
            "root",
            "-v",
            f"{HOST_REPORTS_PATH}:/reports",
            "projectdiscovery/nuclei:latest",
            "-u",
            target,
            "-j",
            "-o",
            f"/reports/nuclei_{scan_id}.json",
            "-v",
        ],
        "zap": [
            "docker",
            "run",
            "--rm",
            "--user",
            "root",
            "-v",
            f"{HOST_REPORTS_PATH}:/zap/wrk:rw",
            "ghcr.io/zaproxy/zaproxy:stable",
            "zap-full-scan.py",
            "-t",
            target,
            "-r",
            f"zap_{scan_id}.html",
            "-d",
        ],
        "giskard": [
            "python",
            "giskard_wrapper.py",
            "--model",
            model_name,
            "--output",
            f"{INTERNAL_REPORTS_PATH}/giskard_{scan_id}.html",
            "--ollama-url",
            "http://host.docker.internal:11434",
        ],
    }


def start_parallel_scans(target: str, scan_id: str, model_info: dict) -> None:
    """Kick off all tool scans in parallel threads."""
    scans_db[scan_id]["status"] = "in_progress"

    actual_model_name = normalize_model_name(model_info["name"])
    commands = build_tool_commands(target, scan_id, actual_model_name)

    for tool, cmd in commands.items():
        thread = threading.Thread(target=run_tool_thread, args=(tool, cmd, scan_id))
        thread.start()

@app.post("/scan/all")
async def start_scan(
    background_tasks: BackgroundTasks,
    target: str = DEFAULT_TARGET,
    model_type: str = DEFAULT_MODEL_TYPE,
    model_name: str = DEFAULT_MODEL_NAME,
):
    """Start a scan for all tools and return the scan ID."""
    scan_id = str(uuid.uuid4())
    scans_db[scan_id] = {
        "target": target,
        "status": "starting",
        "tools": {} 
    }
    
    model_info = {"type": model_type, "name": model_name}
    background_tasks.add_task(start_parallel_scans, target, scan_id, model_info)
    
    return {"scan_id": scan_id, "status": "all_tools_triggered", "target": target}

@app.get("/scan/status/{scan_id}")
async def get_status(scan_id: str):
    """Return the status of a single scan by ID."""
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    return scans_db[scan_id]

@app.get("/scans")
async def get_all_scans():
    """Return all scans currently tracked in memory."""
    return scans_db