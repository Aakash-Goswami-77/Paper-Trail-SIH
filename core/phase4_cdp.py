import cv2
import numpy as np
import hashlib
from dataclasses import dataclass

@dataclass
class CDPVerificationResult:
    authentic: bool
    composite_score: float
    correlation_score: float
    ssim_score: float
    edge_sharpness_variance: float
    reason: str

class CopyDetectionPattern:
    def __init__(self, grid_size: int = 64, block_scale: int = 4):
        self.grid_size = grid_size
        self.block_scale = block_scale

    def generate_cdp_image(self, cert_id: str, output_path: str) -> np.ndarray:
        """
        Generates a deterministic maximum-entropy binary Copy Detection Pattern (CDP)
        seeded by the certificate ID hash.
        """
        hash_bytes = hashlib.sha256(cert_id.encode('utf-8')).digest()
        seed_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        rng = np.random.default_rng(seed_int)

        binary_matrix = rng.integers(0, 2, size=(self.grid_size, self.grid_size), dtype=np.uint8) * 255
        img_high_res = cv2.resize(
            binary_matrix, 
            (self.grid_size * self.block_scale, self.grid_size * self.block_scale), 
            interpolation=cv2.INTER_NEAREST
        )

        cv2.imwrite(output_path, img_high_res)
        return img_high_res

    def _compute_ssim(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Computes structural similarity index between two grayscale images."""
        C1 = (0.01 * 255) ** 2
        C2 = (0.03 * 255) ** 2
        img1 = img1.astype(np.float64)
        img2 = img2.astype(np.float64)
        
        mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
        mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
        
        mu1_sq = mu1 ** 2
        mu2_sq = mu2 ** 2
        mu1_mu2 = mu1 * mu2
        
        sigma1_sq = cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1_sq
        sigma2_sq = cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2_sq
        sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
        
        num = (2 * mu1_mu2 + C1) * (2 * sigma12 + C2)
        den = (mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2)
        ssim_map = num / den
        return float(np.mean(ssim_map))

    def analyze_scan_authenticity(self, original_cert_id: str, scanned_image_path: str) -> CDPVerificationResult:
        """
        Analyzes a scanned physical certificate CDP using multi-dimensional feature fusion 
        (NCC + SSIM + Laplacian Variance) to reliably flag photocopies and counterfeits.
        """
        scanned_img = cv2.imread(scanned_image_path, cv2.IMREAD_GRAYSCALE)
        if scanned_img is None:
            return CDPVerificationResult(
                authentic=False, composite_score=0.0, correlation_score=0.0,
                ssim_score=0.0, edge_sharpness_variance=0.0, reason="Image file unreadable or missing"
            )

        # Re-generate reference template
        hash_bytes = hashlib.sha256(original_cert_id.encode('utf-8')).digest()
        seed_int = int.from_bytes(hash_bytes[:4], byteorder='big')
        rng = np.random.default_rng(seed_int)
        binary_matrix = rng.integers(0, 2, size=(self.grid_size, self.grid_size), dtype=np.uint8) * 255
        reference_img = cv2.resize(
            binary_matrix, 
            (self.grid_size * self.block_scale, self.grid_size * self.block_scale), 
            interpolation=cv2.INTER_NEAREST
        )

        if scanned_img.shape != reference_img.shape:
            scanned_img = cv2.resize(scanned_img, (reference_img.shape[1], reference_img.shape[0]))

        # 1. Normalized Cross-Correlation (NCC)
        ref_norm = reference_img.astype(np.float32) / 255.0
        scan_norm = scanned_img.astype(np.float32) / 255.0
        corr = cv2.matchTemplate(scan_norm, ref_norm, cv2.TM_CCOEFF_NORMED)[0][0]

        # 2. Structural Similarity (SSIM)
        ssim_val = self._compute_ssim(reference_img, scanned_img)

        # 3. High-Frequency Laplacian Variance (Edge blur detection)
        laplacian_var = cv2.Laplacian(scanned_img, cv2.CV_64F).var()

        # Multi-metric composite scoring formula (normalized weights)
        # Weights: 40% Correlation, 40% SSIM, 20% Normalized Sharpness Factor
        sharpness_factor = min(laplacian_var / 300.0, 1.0)
        composite = (0.4 * max(corr, 0)) + (0.4 * max(ssim_val, 0)) + (0.2 * sharpness_factor)

        # Decision Threshold
        is_authentic = bool(composite > 0.45 and laplacian_var > 80.0)

        reason = (
            "Passed multi-metric physical entropy & structure check" 
            if is_authentic 
            else "Failed: Information loss detected (Suspected Photocopy/Counterfeit print)"
        )

        return CDPVerificationResult(
            authentic=is_authentic,
            composite_score=round(composite, 4),
            correlation_score=round(float(corr), 4),
            ssim_score=round(ssim_val, 4),
            edge_sharpness_variance=round(float(laplacian_var), 2),
            reason=reason
        )
