import os
import json
import requests
import cv2
import numpy as np

from core.phase1_keys_schema import process_student_record, generate_degree_only_proof
from core.phase3_watermark import CertificateWatermarker
from core.phase4_cdp import CopyDetectionPattern

BASE_URL = "http://127.0.0.1:8000"
TEMP_DIR = "temp_output"

def ensure_test_assets(sample_raw: dict, processed_sample: dict):
    os.makedirs(TEMP_DIR, exist_ok=True)
    cert_id = sample_raw['cert_id']
    student_name = sample_raw['degree_info']['student_name']
    
    raw_img_path = os.path.join(TEMP_DIR, "raw_cert.png")
    watermarked_img_path = os.path.join(TEMP_DIR, f"{cert_id}_watermarked.png")
    cdp_img_path = os.path.join(TEMP_DIR, f"{cert_id}_cdp.png")

    if not os.path.exists(watermarked_img_path):
        img = np.ones((600, 900, 3), dtype=np.uint8) * 245
        cv2.putText(img, "STATE INSTITUTE OF TECHNOLOGY", (150, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
        cv2.putText(img, f"This is to certify that {student_name}", (100, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        cv2.imwrite(raw_img_path, img)

        watermarker = CertificateWatermarker(scale=25.0)
        watermarker.embed_certificate_watermark(raw_img_path, watermarked_img_path, cert_id)

    if not os.path.exists(cdp_img_path):
        cdp = CopyDetectionPattern()
        cdp.generate_cdp_image(cert_id, cdp_img_path)

    return watermarked_img_path, cdp_img_path

def test_pipeline_api():
    print("=" * 60)
    print(" 🧪 AUTOMATED FASTAPI ENDPOINT TEST SUITE")
    print("=" * 60)

    with open("mock_data.json", "r") as f:
        raw_records = json.load(f)

    sample_raw = raw_records[0]
    processed_sample = process_student_record(sample_raw)
    cert_id = sample_raw["cert_id"]

    proof = generate_degree_only_proof(processed_sample)
    proof["transcript_leaf_hash"] = processed_sample["transcript_group"]["leaf_hash"]

    cert_path, cdp_path = ensure_test_assets(sample_raw, processed_sample)

    print(f"📡 Sending Dual-Image Verification Request for {cert_id}...")

    with open(cert_path, "rb") as cert_file, open(cdp_path, "rb") as cdp_file:
        files = {
            "cert_image": (os.path.basename(cert_path), cert_file, "image/png"),
            "cdp_image": (os.path.basename(cdp_path), cdp_file, "image/png")
        }
        data = {
            "cert_id": cert_id,
            "proof_json": json.dumps(proof)
        }
        
        response = requests.post(f"{BASE_URL}/verify-certificate", data=data, files=files)

    # 🛑 ERROR CATCHING BLOCK ADDED HERE
    if response.status_code != 200:
        print(f"\n❌ API Request Failed! HTTP Status Code: {response.status_code}")
        print("-" * 60)
        print("🛠️ SERVER ERROR TRACEBACK:")
        print(response.text)
        print("-" * 60)
        return

    print("\n" + "-" * 60)
    print(" 📊 SERVER AUDIT RESPONSE BODY")
    print("-" * 60)
    print(json.dumps(response.json(), indent=2))
    print("=" * 60)

if __name__ == "__main__":
    test_pipeline_api()
