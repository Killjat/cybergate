"""
PinchTab HTTP 客户端，统一处理 token 认证
"""
import os
import requests

PINCHTAB_BASE = os.environ.get("PINCHTAB_BASE", "http://localhost:9867")
PINCHTAB_TOKEN = os.environ.get("PINCHTAB_TOKEN", "")

def _headers():
    if PINCHTAB_TOKEN:
        return {"Authorization": f"Bearer {PINCHTAB_TOKEN}"}
    return {}

def pt_get(path, **kwargs):
    return requests.get(f"{PINCHTAB_BASE}{path}", headers=_headers(), timeout=10, **kwargs).json()

def pt_post(path, body=None, **kwargs):
    return requests.post(f"{PINCHTAB_BASE}{path}", json=body or {}, headers=_headers(), timeout=10, **kwargs).json()
