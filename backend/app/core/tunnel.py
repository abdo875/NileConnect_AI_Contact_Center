import re
import subprocess
import threading
import time
from pathlib import Path
from app.core.config import settings
from app.core.logging import logger

_tunnel_process = None

def start_auto_tunnel():
    """
    Checks if PUBLIC_BASE_URL is localhost. If so, automatically spins up
    an SSH tunnel using localhost.run in a background thread, extracts the
    generated public HTTPS URL, overrides settings.PUBLIC_BASE_URL in memory,
    and updates backend/.env for visibility.
    """
    global _tunnel_process

    # Only run if PUBLIC_BASE_URL is localhost / dev mode or a temporary tunnel URL
    is_temp = any(domain in settings.PUBLIC_BASE_URL.lower() for domain in ["localhost", "127.0.0.1", "lhr.life", "ngrok"])
    if not is_temp:
        logger.info("Custom PUBLIC_BASE_URL already configured: %s. Auto-tunnel bypassed.", settings.PUBLIC_BASE_URL)
        return

    def _run_tunnel():
        global _tunnel_process
        cmd = ["ssh", "-o", "StrictHostKeyChecking=no", "-R", "80:localhost:8000", "nokey@localhost.run"]
        logger.info("Starting automatic SSH tunnel via localhost.run...")

        try:
            # Start the ssh tunnel subprocess
            _tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )

            url_pattern = re.compile(r"https://[a-zA-Z0-9-.]+\.lhr\.life")
            
            # Read stdout line by line to extract the tunnel URL
            for line in iter(_tunnel_process.stdout.readline, ""):
                line_str = line.strip()
                match = url_pattern.search(line_str)
                if match:
                    public_url = match.group(0)
                    logger.info("============================================================")
                    logger.info("🚀 AUTOMATIC TUNNEL ESTABLISHED!")
                    logger.info("🔗 Public HTTPS URL: %s", public_url)
                    logger.info("📱 Webhook endpoints are now reachable by Vonage.")
                    logger.info("============================================================")
                    
                    # Update configuration in memory
                    settings.PUBLIC_BASE_URL = public_url
                    
                    break
                
            # Keep reading logs or wait for process completion
            for line in iter(_tunnel_process.stdout.readline, ""):
                if "authenticated" in line.lower() or "tunnel" in line.lower():
                    logger.debug("Tunnel output: %s", line.strip())

        except Exception as e:
            logger.error("Failed to start automatic tunnel: %s", e)

    # Start the runner thread as daemon so it exits with FastAPI
    t = threading.Thread(target=_run_tunnel, daemon=True, name="auto-tunnel")
    t.start()


def stop_auto_tunnel():
    """Terminates the running tunnel subprocess on shutdown."""
    global _tunnel_process
    if _tunnel_process:
        logger.info("Stopping automatic SSH tunnel...")
        try:
            _tunnel_process.terminate()
            _tunnel_process.wait(timeout=2)
            logger.info("Tunnel stopped successfully.")
        except Exception as e:
            logger.error("Error stopping tunnel process: %s", e)
        _tunnel_process = None
