import hashlib
import json

def hash_record(record: dict) -> str:
    """Generates SHA-256 hash of a normalized JSON record."""
    canonical_json = json.dumps(record, sort_keys=True)
    return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()
