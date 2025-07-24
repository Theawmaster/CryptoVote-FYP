from flask import request, jsonify
from functools import wraps
import ipaddress
import os

# Define NTU's trusted IP range(s)
NTU_IP_RANGES = [
    ipaddress.ip_network("155.69.191.0/24"),  # NTU public block
    ipaddress.ip_network("10.0.0.0/8")       # NTU private network block
]

def is_ntu_ip(ip):
    try:
        ip_obj = ipaddress.ip_address(ip)
        return any(ip_obj in net for net in NTU_IP_RANGES)
    except ValueError:
        return False

def ntu_wifi_only(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        # Allow all IPs in development mode
        if os.getenv("FLASK_ENV") == "development":
            print("[DEV MODE] IP restriction bypassed.")
            return f(*args, **kwargs)

        # Get client IP (accounting for reverse proxies)
        client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
        print(f"🔒 Checking NTU WiFi access for IP: {client_ip}")

        if not is_ntu_ip(client_ip):
            return jsonify({
                "error": "Access restricted to NTU WiFi only.",
                "your_ip": client_ip
            }), 403

        return f(*args, **kwargs)
    return wrapper
