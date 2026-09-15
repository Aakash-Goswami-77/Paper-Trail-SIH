import json
import os
import cv2
import numpy as np
import hashlib
from core.phase1_keys_schema import process_student_record, generate_degree_only_proof, verify_degree_only_proof, DegreeInfo
from core.phase2_merkle import MerkleTree, RevocationList, PolygonAmoyProvider
from core.phase3_watermark import CertificateWatermarker

def create_sample_certificate_image(output_path: str, student_name: str, cert_id: str):
    img = np.ones((600, 900, 3), dtype=np.uint8) * 245
    cv2.putText(img, "STATE INSTITUTE OF TECHNOLOGY", (150, 80), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (20, 20, 20), 2)
    cv2.putText(img, "CERTIFICATE OF GRADUATION", (220, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (50, 50, 50), 2)
    cv2.putText(img, f"This is to certify that {student_name}", (100, 260), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(img, f"Certificate ID: {cert_id}", (100, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (100, 100, 100), 1)
    cv2.imwrite(output_path, img)

def main():
    print("=" * 60)
    print(" 🚀 FULL PIPELINE INTEGRATION: PHASES 1, 2, & 3")
    print("=" * 60)

    mock_path = "mock_data.json"
    if not os.path.exists(mock_path):
        print(f"❌ Error: {mock_path} not found.")
        return

    with open(mock_path, "r") as f:
        raw_records = json.load(f)

    print(f"📂 Loaded {len(raw_records)} student records.")

    leaves = []
    processed_records = []
    revocation_list = RevocationList(size=len(raw_records))

    for raw in raw_records:
        processed = process_student_record(raw)
        processed_records.append(processed)
        
        # Composite Leaf Hash using sorted combination to match Merkle standards
        d_hash = processed["degree_group"]["leaf_hash"]
        t_hash = processed["transcript_group"]["leaf_hash"]
        combined_pair = "".join(sorted([d_hash, t_hash]))
        composite_leaf = hashlib.sha256(combined_pair.encode('utf-8')).hexdigest()
        leaves.append(composite_leaf)

        # Skip revocation for index 0 so it tests as valid (not revoked)
        status_idx = raw.get("status_index", 0)
        if status_idx > 0 and status_idx % 3 == 0:
            revocation_list.revoke(status_idx)

    print(f"🔒 Phase 1 Complete: Generated {len(leaves)} salted composite Merkle leaves.")

    merkle_tree = MerkleTree(leaves)
    root_hash = merkle_tree.root
    print(f"🌳 Phase 2 Complete: Merkle Root Calculated -> {root_hash}")

    provider = PolygonAmoyProvider()
    tx_hash = provider.anchor_root(root_hash, "ipfs://QmMockRevocationListUriHash")
    print(f"⛓️ Blockchain Anchored! Mock Tx Hash: {tx_hash}")

    print("\n" + "-" * 60)
    print(" 🌊 RUNNING PHASE 3: DIGITAL DWT/DCT/SVD WATERMARKING")
    print("-" * 60)

    sample_student = processed_records[0]
    sample_raw = raw_records[0]
    cert_id = sample_raw['cert_id']
    student_name = sample_raw['degree_info']['student_name']

    os.makedirs("temp_output", exist_ok=True)
    raw_img_path = "temp_output/raw_cert.png"
    watermarked_img_path = f"temp_output/{cert_id}_watermarked.png"

    create_sample_certificate_image(raw_img_path, student_name, cert_id)

    watermarker = CertificateWatermarker(scale=25.0)
    watermarker.embed_certificate_watermark(raw_img_path, watermarked_img_path, cert_id)
    print(f"💧 Embedded Invisible Watermark into asset for: {student_name} ({cert_id})")

    extracted_cert_id = watermarker.extract_certificate_watermark(watermarked_img_path, payload_length_chars=len(cert_id))
    watermark_matched = (extracted_cert_id == cert_id)

    print(f"   - Extracted Payload:           '{extracted_cert_id}'")
    print(f"   - Watermark Match Verification: {'✅ PASSED' if watermark_matched else '❌ FAILED'}")

    print("\n" + "=" * 60)
    print(" 🎯 COMPOSITE VERIFICATION AUDIT RESULTS")
    print("=" * 60)
    
    proof = generate_degree_only_proof(sample_student)
    deg_hash, trans_hash = verify_degree_only_proof(proof)
    reconstructed_pair = "".join(sorted([deg_hash, sample_student["transcript_group"]["leaf_hash"]]))
    reconstructed_composite = hashlib.sha256(reconstructed_pair.encode('utf-8')).hexdigest()
    
    is_valid_leaf = reconstructed_composite in merkle_tree.leaves
    is_revoked = revocation_list.is_revoked(sample_raw.get("status_index", 0))

    print(f"   1. Merkle Leaf & Root Integrity: {'✅ VALID' if is_valid_leaf else '❌ INVALID'}")
    print(f"   2. Revocation Status Check:     {'🔴 REVOKED' if is_revoked else '🟢 VALID (Not Revoked)'}")
    print(f"   3. Digital Tamper Watermark:    {'✅ AUTHENTIC' if watermark_matched else '❌ TAMPERED'}")
    print("=" * 60)

if __name__ == "__main__":
    main()
