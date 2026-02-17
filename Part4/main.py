import threading
from fastapi import FastAPI, BackgroundTasks, HTTPException
import subprocess
import os
import uuid
from typing import Dict
import time

app = FastAPI(title="Parallel Security Scanner")
scans_db: Dict[str, dict] = {}

# --- הגדרות נתיבים ---
# 1. הנתיב במחשב המארח (Windows) - עבור דוקרים חיצוניים (Zap, Nuclei, Wapiti)
HOST_REPORTS_PATH = "E:/cyber-project/vulnerabilities-report-app/docker/reports"

# 2. הנתיב בתוך הקונטיינר הנוכחי - עבור Giskard וסקריפטים פנימיים
INTERNAL_REPORTS_PATH = "/reports"

# יצירת התיקייה הפנימית אם אינה קיימת
if not os.path.exists(INTERNAL_REPORTS_PATH):
    try:
        os.makedirs(INTERNAL_REPORTS_PATH)
    except:
        pass

def run_tool_thread(tool_name: str, command: list, scan_id: str):
    scans_db[scan_id]["tools"][tool_name] = "in_progress"
    
    try:
        print(f"[{tool_name}] Preparing to start...")
        
        # הרצה של הפקודה (עובד גם לרשימה וגם לסקריפט פייתון)
        # עבור Giskard אנחנו מריצים פקודה פשוטה, לאחרים דוקר
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        
        # הדפסת לוגים (מקוצרת כדי לא להעמיס)
        if result.stdout:
            print(f"[{tool_name}] STDOUT: {result.stdout[:500]}...") 

        if result.stderr:
            print(f"[{tool_name}] STDERR:\n{result.stderr}")

        if result.returncode != 0:
            # טיפול מיוחד באזהרות של ZAP
            if tool_name == "zap" and result.returncode == 2:
                scans_db[scan_id]["tools"][tool_name] = "finished"
            else:
                print(f"!!! Error in {tool_name} (Exit Code {result.returncode}) !!!")
                scans_db[scan_id]["tools"][tool_name] = "failed"
        else:
            print(f"[{tool_name}] Finished successfully.")
            scans_db[scan_id]["tools"][tool_name] = "finished"

    except Exception as e:
        print(f"Critical Exception in {tool_name}: {e}")
        scans_db[scan_id]["tools"][tool_name] = "failed"
    
    check_overall_status(scan_id)

def check_overall_status(scan_id: str):
    statuses = scans_db[scan_id]["tools"].values()
    if "in_progress" not in statuses:
        if "failed" in list(statuses):
            scans_db[scan_id]["status"] = "finished_with_errors"
        else:
            scans_db[scan_id]["status"] = "completed"

def start_parallel_scans(target: str, scan_id: str, model_info: dict):
    scans_db[scan_id]["status"] = "in_progress"
    
    # תיקון שם המודל ל-Ollama (הוספת :latest אם חסר)
    actual_model_name = model_info["name"]
    if ":" not in actual_model_name:
        actual_model_name += ":latest"

    commands = {
        "wapiti": [
            "docker", "run", "--rm", 
            "-v", f"{HOST_REPORTS_PATH}:/reports",
            "cyberwatch/wapiti", 
            "-u", target, 
            "-f", "html",                
            "-o", f"/reports/wapiti_{scan_id}.html", 
            "--depth", "2", 
            "--max-links-per-page", "5", 
            "--timeout", "3", 
            "--scope", "folder", 
            "-m", "xss,sql,exec,file"
        ],
        "nuclei": [
            "docker", "run", "--rm", 
            "--user", "root",  
            "-v", f"{HOST_REPORTS_PATH}:/reports",
            "projectdiscovery/nuclei:latest", 
            "-u", target, 
            "-j",                        
            "-o", f"/reports/nuclei_{scan_id}.json"
        ],
        "zap": [
            "docker", "run", "--rm", 
            "--user", "root", 
            "-v", f"{HOST_REPORTS_PATH}:/zap/wrk:rw",
            "ghcr.io/zaproxy/zaproxy:stable", "zap-baseline.py", "-t", target, "-r", f"zap_{scan_id}.html"
        ],
        # --- Giskard רץ כסקריפט פנימי ---
        "giskard": [
            "python", "giskard_wrapper.py",
            "--model", actual_model_name,
            # נתיב פנימי לקובץ הדוח
            "--output", f"{INTERNAL_REPORTS_PATH}/giskard_{scan_id}.html",
            # כתובת פנימית ל-Docker כדי להגיע ל-Ollama במחשב
            "--ollama-url", "http://host.docker.internal:11434"
        ]
    }

    for tool, cmd in commands.items():
        thread = threading.Thread(target=run_tool_thread, args=(tool, cmd, scan_id))
        thread.start()

@app.post("/scan/all")
async def start_scan(
    background_tasks: BackgroundTasks,
    target: str = "http://testphp.vulnweb.com", # כתובת ברירת מחדל
    model_type: str = "ollama", 
    model_name: str = "llama3"
):
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
    if scan_id not in scans_db:
        raise HTTPException(status_code=404, detail="Scan ID not found")
    return scans_db[scan_id]

@app.get("/scans")
async def get_all_scans():
    return scans_db