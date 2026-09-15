import numpy as np

def extract_and_verify_watermark(image_path: str) -> tuple[bool, float, str]:
    """Simulates DWT fragile watermark verification."""
    if "tampered" in image_path.lower():
        return False, 0.02, "Pixel manipulation detected in transcript region. DWT fragile watermark signal destroyed."
    return True, 0.89, "DWT fragile watermark signal intact."
