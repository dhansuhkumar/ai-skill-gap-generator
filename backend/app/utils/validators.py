# backend/app/utils/validators.py

def require_keys(json_data, keys):
    missing = [k for k in keys if k not in json_data]
    if missing:
        raise ValueError(f"Missing keys: {missing}")