import os
from fastapi import APIRouter, HTTPException

log_router = APIRouter()

LOG_FILE_PATH = 'app.log'

# Debugging: Log the log file path
# print(f"Log file path (logs.py): {LOG_FILE_PATH}")

@log_router.get("/logs")
async def get_logs():
    if not os.path.exists(LOG_FILE_PATH):
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        with open(LOG_FILE_PATH, "r") as log_file:
            logs = log_file.read()
        return {"logs": logs}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error reading log file")
