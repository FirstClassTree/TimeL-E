#!/usr/bin/env python3
import os
import sys
import requests

port  = int(os.getenv("ML_SERVICE_PORT", "8001"))

try:
    response = requests.get(f"http://localhost:{port}/health", timeout=10)
    if response.status_code == 200 and response.json().get('status') == 'healthy':
        sys.exit(0)
    else:
        sys.exit(1)
except:
    sys.exit(1)
