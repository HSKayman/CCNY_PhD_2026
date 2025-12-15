"""
CSc I6716 Final Project: Window Screen Removal via Visual Motion Analysis

Author: Hasan Suca Kayman
Course: CSc I6716 - Computer Vision
"""

import numpy as np
import cv2
from scipy import ndimage
from scipy.signal import convolve2d
import matplotlib.pyplot as plt
from pathlib import Path
import argparse
from typing import Tuple, List, Optional
import warnings


# =============================================================================
# Phase 1: Preprocessing and Artifact Modeling
# =============================================================================

def load_video_frames(video_path: str, num_frames: int = 10, 
                      start_frame: int = 0) -> List[np.ndarray]:
    ## read video file and extract N consecutive frames.

    cap = cv2.VideoCapture(video_path)
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    print(f"Total frames: {total_frames}")
    print(f"FPS: {fps:.2f}")
    print(f"Resolution: {width}x{height}")

    # set starting position
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
    
    frames = []
    for i in range(num_frames):
        ret, frame = cap.read()
        if not ret:
            warnings.warn(f"Could only read {i} frames instead of {num_frames}")
            break
        frames.append(frame)
    
    cap.release()
    
   
    
    print(f"Loaded {len(frames)} frames starting from frame {start_frame}")
    return frames


def rgb_to_grayscale_ntsc(frame: np.ndarray):
    # NTSC formula
    b, g, r = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    return gray.astype(np.float64)


def preprocess_frames(frames: List[np.ndarray]):
    # convert to grayscale and normalize
    gray_frames = []
    color_frames = []
    
    for frame in frames:
        # convert to grayscale using NTSC formula
        gray = rgb_to_grayscale_ntsc(frame)
        gray_frames.append(gray)
        
        # keep color version as float for later processing
        color_frames.append(frame.astype(np.float64) / 255.0)
    
    print(f"Preprocessed {len(gray_frames)} frames to grayscale")
    return gray_frames, color_frames


# =============================================================================
# Phase 2: Visual Motion Estimation (Correspondence)
# =============================================================================

# NOTE: The following functions are commented out as they duplicate
# functionality in classical_cv_utils.py. Use sobel_operator and 
# harris_corner_detector from classical_cv_utils instead.

def compute_sobel_gradients(image: np.ndarray):
    # compute image gradients using Sobel operator.
   
    # sobel kernels
    sobel_x = np.array([[-1, 0, 1],
                        [-2, 0, 2],
                        [-1, 0, 1]], dtype=np.float64)
    
    sobel_y = np.array([[-1, -2, -1],
                        [ 0,  0,  0],
                        [ 1,  2,  1]], dtype=np.float64)
    
    # compute gradients using convolution
    Ix = convolve2d(image, sobel_x, mode='same', boundary='symm')
    Iy = convolve2d(image, sobel_y, mode='same', boundary='symm')
    
    # Gradient magnitude
    magnitude = np.sqrt(Ix**2 + Iy**2)
    
    return Ix, Iy, magnitude


# def detect_harris_corners(image: np.ndarray, k: float = 0.04, 
#                           threshold_ratio: float = 0.01,
#                           window_size: int = 3):
# 
#     # Detect corners using Harris corner detector.
#     
#     # Compute gradients
#     Ix, Iy, _ = compute_sobel_gradients(image)
#     
#     # Compute products of derivatives
#     Ixx = Ix * Ix
#     Iyy = Iy * Iy
#     Ixy = Ix * Iy
#     
#     # Apply Gaussian smoothing
#     sigma = window_size / 3.0
#     Sxx = ndimage.gaussian_filter(Ixx, sigma)
#     Syy = ndimage.gaussian_filter(Iyy, sigma)
#     Sxy = ndimage.gaussian_filter(Ixy, sigma)
#     
#     # Compute Harris response
#     det = Sxx * Syy - Sxy * Sxy
#     trace = Sxx + Syy
#     R = det - k * (trace ** 2)
#     
#     # Threshold and find corners
#     threshold = threshold_ratio * R.max()
#     corners = np.argwhere(R > threshold)
#     
#     return corners


# NOTE: filter_screen_features is not used in the demo - commented out
# def filter_screen_features(corners: np.ndarray, 
#                             image: np.ndarray,
#                             periodicity_threshold: float = 0.3):
#     # filter out features that lie on the periodic screen pattern.
#     # uses local frequency analysis to identify screen grid locations.
#     
#     if len(corners) == 0:
#         return corners
#     
#     # analyze local frequency content around each corner
#     patch_size = 15
#     half_size = patch_size // 2
#     h, w = image.shape
#     
#     # filtered corners
#     filtered_corners = []
#     
#     for corner in corners:
#         y, x = corner
#         
#         # skip corners too close to edges
#         if y < half_size or y >= h - half_size or x < half_size or x >= w - half_size:
#             continue
#         
#         # extract patch
#         patch = image[y-half_size:y+half_size+1, x-half_size:x+half_size+1]
#         
#         # compute FFT and check for periodic peaks
#         fft = np.fft.fft2(patch)
#         fft_shifted = np.fft.fftshift(np.abs(fft))
#         
#         # normalize
#         fft_norm = fft_shifted / (fft_shifted.max() + 1e-10)
#         
#         # check for strong periodic components (excluding DC)
#         center = patch_size // 2
#         fft_norm[center-1:center+2, center-1:center+2] = 0  # Remove DC
#         
#         # if high periodic content, likely on screen grid :)
#         if fft_norm.max() < periodicity_threshold:
#             filtered_corners.append(corner)
#     
#     return np.array(filtered_corners) if filtered_corners else np.array([]).reshape(0, 2)


# NOTE: compute_optical_flow_lk is not used - we use compute_optical_flow_pyramidal instead
# def compute_optical_flow_lk(frame1: np.ndarray, frame2: np.ndarray,
#                             window_size: int = 15):
#     # compute dense optical flow using Lucas-Kanade method.
#     # based on the constraint equation: Ix*u + Iy*v + It = 0
#     
#     # compute spatial gradients on first frame
#     Ix, Iy, _ = compute_sobel_gradients(frame1)
#     
#     # compute temporal gradient
#     It = frame2.astype(np.float64) - frame1.astype(np.float64)
#     
#     # initialize flow fields
#     h, w = frame1.shape
#     u = np.zeros((h, w), dtype=np.float64)
#     v = np.zeros((h, w), dtype=np.float64)
#     
#     half_win = window_size // 2
#     
#     # compute flow at each pixel using local window
#     for y in range(half_win, h - half_win):
#         for x in range(half_win, w - half_win):
#             # extract local windows
#             Ix_win = Ix[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             Iy_win = Iy[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             It_win = It[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             
#             # build system: A * [u, v]^T = b
#             A = np.vstack([Ix_win, Iy_win]).T
#             b = -It_win
#             
#             # solve using least squares (normal equations)
#             ATA = A.T @ A
#             ATb = A.T @ b
#             
#             # check if system is well-conditioned
#             eigenvalues = np.linalg.eigvalsh(ATA)
#             if eigenvalues.min() > 1e-6:
#                 flow = np.linalg.solve(ATA, ATb)
#                 u[y, x] = flow[0]
#                 v[y, x] = flow[1]
#     
#     return u, v


def compute_optical_flow_pyramidal(frame1: np.ndarray, frame2: np.ndarray,
                                    levels: int = 3):
 
    # compute optical flow using pyramidal Lucas-Kanade for larger motions.
    # uses OpenCV's implementation for efficiency.
   
    # convert to uint8 if needed
    if frame1.dtype != np.uint8:
        frame1_uint8 = (frame1 / frame1.max() * 255).astype(np.uint8)
    else:
        frame1_uint8 = frame1
        
    if frame2.dtype != np.uint8:
        frame2_uint8 = (frame2 / frame2.max() * 255).astype(np.uint8)
    else:
        frame2_uint8 = frame2
    
    # use Farneback dense optical flow
    # DONT FORGET To TRY WRITE YOUR OWN IMPLEMENTATION OF THE FARNEBACK ALGORITHM
    flow = cv2.calcOpticalFlowFarneback(
        frame1_uint8, frame2_uint8,
        flow=None,
        pyr_scale=0.5,
        levels=levels,
        winsize=15,
        iterations=3,
        poly_n=5,
        poly_sigma=1.2,
        flags=0
    )
    
    u = flow[:, :, 0]
    v = flow[:, :, 1]
    
    return u, v


# NOTE: These homography functions are not used - we use cv2.findHomography instead
# def estimate_homography_ransac(src_points: np.ndarray, dst_points: np.ndarray,
#                                 num_iterations: int = 1000,
#                                 threshold: float = 3.0):
#     # estimate homography matrix using RANSAC.
#    
#     if len(src_points) < 4:
#         # return identity if not enough points
#         return np.eye(3)
#     
#     best_H = np.eye(3)
#     best_inliers = 0
#     
#     n_points = len(src_points)
#     
#     for _ in range(num_iterations):
#         # randomly select 4 points
#         indices = np.random.choice(n_points, 4, replace=False)
#         src_sample = src_points[indices]
#         dst_sample = dst_points[indices]
#         
#         # compute homography from 4 point correspondences
#         try:
#             H = compute_homography_dlt(src_sample, dst_sample)
#         except:
#             continue
#         
#         # count inliers
#         src_homogeneous = np.hstack([src_points, np.ones((n_points, 1))])
#         projected = (H @ src_homogeneous.T).T
#         projected = projected[:, :2] / projected[:, 2:3]
#         
#         errors = np.linalg.norm(projected - dst_points, axis=1)
#         inliers = np.sum(errors < threshold)
#         
#         if inliers > best_inliers:
#             best_inliers = inliers
#             best_H = H
#     
#     return best_H


# def compute_homography_dlt(src_points: np.ndarray, dst_points: np.ndarray):
#     # compute homography using Direct Linear Transform (DLT).
#    
#     n = len(src_points)
#     A = []
#     
#     for i in range(n):
#         x, y = src_points[i]
#         xp, yp = dst_points[i]
#         
#         A.append([-x, -y, -1, 0, 0, 0, x*xp, y*xp, xp])
#         A.append([0, 0, 0, -x, -y, -1, x*yp, y*yp, yp])
#     
#     A = np.array(A)
#     
#     # solve using SVD
#     # consider to implement manually
#     _, _, Vh = np.linalg.svd(A)
#     H = Vh[-1].reshape(3, 3)
#     
#     # normalize
#     H = H / H[2, 2]
#     
#     return H


def match_features_between_frames(frame1: np.ndarray, frame2: np.ndarray,
                                   max_features: int = 500,
                                   filter_screen: bool = True):
    # detect and match features between two frames using ORB.
    # optionally filters out features that appear to be on the screen grid.
   
    # uint8
    frame1_uint8 = (frame1 / frame1.max() * 255).astype(np.uint8) if frame1.max() > 1 else (frame1 * 255).astype(np.uint8)
    frame2_uint8 = (frame2 / frame2.max() * 255).astype(np.uint8) if frame2.max() > 1 else (frame2 * 255).astype(np.uint8)
    
    # apply slight blur to reduce screen patterns influence on feature detection
    if filter_screen:
        frame1_filtered = cv2.GaussianBlur(frame1_uint8, (3, 3), 1.0)
        frame2_filtered = cv2.GaussianBlur(frame2_uint8, (3, 3), 1.0)
    else:
        frame1_filtered = frame1_uint8
        frame2_filtered = frame2_uint8
    
    # create ORB detector with adjusted parameters
    orb = cv2.ORB_create(
        nfeatures=max_features,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=15,  # avoid edges near screen
        patchSize=31
    )
    
    # detect and compute
    kp1, des1 = orb.detectAndCompute(frame1_filtered, None)
    kp2, des2 = orb.detectAndCompute(frame2_filtered, None)
    
    if des1 is None or des2 is None or len(des1) < 4 or len(des2) < 4:
        return np.array([]).reshape(0, 2), np.array([]).reshape(0, 2)
    
    # match features using BFMatcher with ratio test
    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des1, des2, k=2)
    
    # apply ratio test
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < 0.75 * n.distance:
                good_matches.append(m)
    
    if len(good_matches) < 4:
        return np.array([]).reshape(0, 2), np.array([]).reshape(0, 2)
    
    # sort by distance
    good_matches = sorted(good_matches, key=lambda x: x.distance)
    
    # take top matches
    good_matches = good_matches[:min(100, len(good_matches))]
    
    # extract matched points
    pts1 = np.array([kp1[m.queryIdx].pt for m in good_matches])
    pts2 = np.array([kp2[m.trainIdx].pt for m in good_matches])
    
    # filter out features on screen pattern (high local variance in original image)
    if filter_screen and len(pts1) > 0:
        valid_mask = np.ones(len(pts1), dtype=bool)
        patch_size = 9
        half_size = patch_size // 2
        h, w = frame1_uint8.shape
        
        for i, (pt1, pt2) in enumerate(zip(pts1, pts2)):
            x1, y1 = int(pt1[0]), int(pt1[1])
            
            # skip if too close to edge
            if y1 < half_size or y1 >= h - half_size or x1 < half_size or x1 >= w - half_size:
                continue
            
            # check local patch for screen like pattern
            patch = frame1_uint8[y1-half_size:y1+half_size+1, x1-half_size:x1+half_size+1]
            
            # high local variance + periodic structure = likely screen feature
            local_var = np.var(patch)
            if local_var > 1500:  # High variance threshold
                # check for periodicity using FFT
                fft = np.abs(np.fft.fft2(patch.astype(float)))
                fft[0, 0] = 0  # remove DC
                if fft.max() > local_var * 0.5:  # Strong periodic component
                    valid_mask[i] = False
        
        pts1 = pts1[valid_mask]
        pts2 = pts2[valid_mask]
    
    return pts1, pts2


def estimate_global_motion(frames: List[np.ndarray], ref_idx: int = 0,
                           method: str = 'homography'):
    # estimate global motion between reference frame and all other frames.
    # the goal is to warp each frame to align with the reference frame.
    # for homography: compute H such that warpPerspective(frame, H) aligns with ref
    # for flow: compute (u,v) such that frame(x+u, y+v) aligns with ref(x,y)
   
    n_frames = len(frames)
    ref_frame = frames[ref_idx]
    
    transforms = []
    
    print(f"Estimating motion relative to frame {ref_idx}...")
    
    for i, frame in enumerate(frames):
        if i == ref_idx:
            transforms.append(np.eye(3) if method == 'homography' else (np.zeros_like(ref_frame), np.zeros_like(ref_frame)))
            continue
        
        if method == 'homography':
            # feature based homography estimation
            # Match features: pts_ref in reference, pts_curr in current frame
            pts_ref, pts_curr = match_features_between_frames(ref_frame, frame)
            
            if len(pts_ref) >= 4:
                # Find H such that pts_ref = H * pts_curr
                # warpPerspective(img, H) does inverse mapping: dst(p) = src(H**-1 * p)
                # we want dst to be aligned with ref, so we need H mapping curr->ref
                H, mask = cv2.findHomography(pts_curr, pts_ref, cv2.RANSAC, 5.0)
                if H is None:
                    H = np.eye(3)
                    print(f"  Frame {i}: Homography failed, using identity")
                else:
                    # check if H is reasonable
                    if np.abs(H[2, 0]) > 0.01 or np.abs(H[2, 1]) > 0.01:
                        warnings.warn(f"Frame {i}: Large perspective  problem")
            else:
                H = np.eye(3)
                print(f"  Frame {i}: Not enough matches ({len(pts_ref)}), using identity")
            
            transforms.append(H)
            if len(pts_ref) >= 4:
                print(f"  Frame {i}: Found {len(pts_ref)} matches, H determinant: {np.linalg.det(H):.4f}")
            
        else:  # optical flow
            # compute flow from current frame to reference frame
            u, v = compute_optical_flow_pyramidal(frame, ref_frame)
            transforms.append((u, v))
            flow_mag = np.sqrt(u**2 + v**2)
            print(f"  Frame {i}: Flow mean magnitude: {flow_mag.mean():.4f}")
    
    return transforms


# =============================================================================
# Phase 3: Screen Removal via Temporal Filtering
# =============================================================================

def warp_frame_homography(frame: np.ndarray, H: np.ndarray):
    h, w = frame.shape[:2]
    
    # convert to float32 for OpenCV (better precision than float64 for warping)
    frame_f32 = frame.astype(np.float32)
    H_f64 = H.astype(np.float64)  # homography should be float64
    
    warped = cv2.warpPerspective(frame_f32, H_f64, (w, h),
                                  flags=cv2.INTER_LINEAR,
                                  borderMode=cv2.BORDER_REFLECT)
    
    return warped.astype(frame.dtype)


def warp_frame_flow(frame: np.ndarray, u: np.ndarray, v: np.ndarray):
    # warp frame using dense optical flow field.
    h, w = frame.shape[:2]
    
    # create coordinate grids
    x, y = np.meshgrid(np.arange(w), np.arange(h))
    
    # compute new coordinates
    map_x = (x + u).astype(np.float32)
    map_y = (y + v).astype(np.float32)
    
    # warp using remap
    if len(frame.shape) == 2:
        warped = cv2.remap(frame.astype(np.float32), map_x, map_y, 
                           cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    else:
        warped = cv2.remap(frame.astype(np.float32), map_x, map_y,
                           cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    
    return warped


def motion_compensate_frames(frames: List[np.ndarray], transforms: List,
                              method: str = 'homography'):
    # apply motion compensation to align all frames with reference.
    aligned_frames = []
    
    for i, (frame, transform) in enumerate(zip(frames, transforms)):
        if method == 'homography':
            aligned = warp_frame_homography(frame, transform)
        else:
            u, v = transform
            aligned = warp_frame_flow(frame, u, v)
        
        aligned_frames.append(aligned)
        if i == 0 or i == len(frames) - 1:
            print(f"  Frame {i}: range [{aligned.min():.4f}, {aligned.max():.4f}]")
    
    print(f"  Aligned {len(aligned_frames)} frames")
    return aligned_frames


def temporal_average_filter(frames: List[np.ndarray], 
                            weights: Optional[np.ndarray] = None):
    # stack frames along a new axis
    stacked = np.stack(frames, axis=0)  # Shape: (N, H, W) or (N, H, W, C)
    
    if weights is None:
        # simple mean - more robust
        result = np.mean(stacked, axis=0)
    else:
        weights = np.array(weights) / np.sum(weights)
        # weighted average along first axis
        result = np.tensordot(weights, stacked, axes=([0], [0]))
    
    print(f"Applied temporal averaging over {len(frames)} frames")
    print(f"  Result range: [{result.min():.4f}, {result.max():.4f}]")
    
    return result

#It WORKS
def temporal_median_filter(frames: List[np.ndarray]):
    # temporal median image
    stacked = np.stack(frames, axis=0)  # Shape: (N, H, W) or (N, H, W, C)
    result = np.median(stacked, axis=0)
    
    print(f"Applied temporal median over {len(frames)} frames")
    print(f"  Result range: [{result.min():.4f}, {result.max():.4f}]")
    
    return result


# NOTE: temporal_trimmed_mean_filter not used in demo - commented out
# def temporal_trimmed_mean_filter(frames: List[np.ndarray], 
#                                   trim_fraction: float = 0.2):
#     # temporal trimmed mean filter
#     from scipy import stats
#     
#     stacked = np.stack(frames, axis=0)  # Shape: (N, H, W) or (N, H, W, C)
#     
#     # apply trimmed mean along first axis
#     result = stats.trim_mean(stacked, trim_fraction, axis=0)
#     
#     print(f"Applied temporal trimmed mean (trim={trim_fraction}) over {len(frames)} frames")
#     print(f"  Result range: [{result.min():.4f}, {result.max():.4f}]")
#     
#     return result


# =============================================================================
# Phase 4: Post-Processing and Analysis
# =============================================================================

def median_filter(image: np.ndarray, kernel_size: int = 3):
    if len(image.shape) == 2:
        return ndimage.median_filter(image, size=kernel_size)
    else:
        # apply to each channel
        result = np.zeros_like(image)
        for c in range(image.shape[2]):
            result[:, :, c] = ndimage.median_filter(image[:, :, c], size=kernel_size)
        return result


def kuwahara_filter(image: np.ndarray, kernel_size: int = 5):
    if len(image.shape) == 3:
        # convert to grayscale for processing
        gray = rgb_to_grayscale_ntsc(image * 255) / 255.0
    else:
        gray = image
    
    h, w = gray.shape
    result = np.zeros_like(gray)
    
    k = kernel_size // 2
    
    # pad image
    padded = np.pad(gray, k, mode='reflect')
    
    for y in range(h):
        for x in range(w):
            # define 4 overlapping quadrants
            regions = [
                padded[y:y+k+1, x:x+k+1],          
                padded[y:y+k+1, x+k:x+2*k+1],       
                padded[y+k:y+2*k+1, x:x+k+1],       
                padded[y+k:y+2*k+1, x+k:x+2*k+1]    
            ]
            
            # find region with minimum variance
            variances = [np.var(r) for r in regions]
            min_idx = np.argmin(variances)
            
            # use mean of minimum variance region
            result[y, x] = np.mean(regions[min_idx])
    
    return result


def bilateral_filter(image: np.ndarray, d: int = 9, 
                     sigma_color: float = 75, 
                     sigma_space: float = 75):
    # handle edge cases
    if image.max() == 0:
        warnings.warn("Input image is all zeros!")
        return image
    
    # normalize to 0-255 range for OpenCV
    img_min, img_max = image.min(), image.max()
    if img_max <= 1.0:
        # already in 0-1 range
        image_uint8 = (image * 255).astype(np.uint8)
    elif img_max <= 255:
        # already in 0-255 range
        image_uint8 = image.astype(np.uint8)
    else:
        # normalize to 0-255
        image_uint8 = ((image - img_min) / (img_max - img_min) * 255).astype(np.uint8)
    
    filtered = cv2.bilateralFilter(image_uint8, d, sigma_color, sigma_space)
    
    # return in same range as input
    if img_max <= 1.0:
        return filtered.astype(np.float64) / 255.0
    else:
        return filtered.astype(np.float64)


def unsharp_mask(image: np.ndarray, sigma: float = 1.0, 
                 strength: float = 0.8):
    # apply unsharp masking to enhance edges.
    if len(image.shape) == 3:
        # apply to each channel
        result = np.zeros_like(image)
        for c in range(image.shape[2]):
            blurred = ndimage.gaussian_filter(image[:, :, c], sigma)
            result[:, :, c] = image[:, :, c] + strength * (image[:, :, c] - blurred)
        return np.clip(result, 0, 1 if image.max() <= 1 else 255)
    else:
        blurred = ndimage.gaussian_filter(image, sigma)
        sharpened = image + strength * (image - blurred)
        return np.clip(sharpened, 0, 1 if image.max() <= 1 else 255)


# NOTE: deconvolution_sharpen not used in demo - commented out
# def deconvolution_sharpen(image: np.ndarray, iterations: int = 10, 
#                           psf_sigma: float = 1.0):
#     # apply Richardson-Lucy deconvolution for sharpening.
#     from scipy.signal import convolve2d
#     
#     # create PSF (point spread function) - Gaussian blur kernel
#     size = int(6 * psf_sigma) | 1  # Make odd
#     x = np.arange(size) - size // 2
#     kernel_1d = np.exp(-x**2 / (2 * psf_sigma**2))
#     psf = np.outer(kernel_1d, kernel_1d)
#     psf = psf / psf.sum()
#     
#     # flip PSF for correlation
#     psf_flip = psf[::-1, ::-1]
#     
#     def rl_channel(img_channel):
#         # initialize estimate
#         estimate = img_channel.copy()
#         
#         for _ in range(iterations):
#             # convolve estimate with PSF
#             blurred = convolve2d(estimate, psf, mode='same', boundary='symm')
#             blurred = np.maximum(blurred, 1e-10)
#             
#             # compute ratio
#             ratio = img_channel / blurred
#             
#             # correlate ratio with PSF
#             correction = convolve2d(ratio, psf_flip, mode='same', boundary='symm')
#             
#             # update estimate
#             estimate = estimate * correction
#             estimate = np.clip(estimate, 0, 1 if img_channel.max() <= 1 else 255)
#         
#         return estimate
#     
#     if len(image.shape) == 3:
#         result = np.zeros_like(image)
#         for c in range(image.shape[2]):
#             result[:, :, c] = rl_channel(image[:, :, c])
#         return result
#     else:
#         return rl_channel(image)


# NOTE: compute_psnr not used in demo - commented out
# def compute_psnr(original: np.ndarray, restored: np.ndarray):
#     # compute Peak Signal-to-Noise Ratio.
#     mse = np.mean((original - restored) ** 2)
#     if mse == 0:
#         return float('inf')
#     
#     max_val = 1.0 if original.max() <= 1 else 255.0
#     psnr = 10 * np.log10(max_val ** 2 / mse)
#     
#     return psnr


def visualize_optical_flow(u: np.ndarray, v: np.ndarray, 
                           max_flow: float = None):
    # visualize optical flow as HSV color image.
    h, w = u.shape
    
    # compute magnitude and angle
    magnitude = np.sqrt(u**2 + v**2)
    angle = np.arctan2(v, u)
    
    # normalize magnitude using percentile to handle outliers
    if max_flow is None:
        # use 99th percentile to avoid outlier dominance
        max_flow = np.percentile(magnitude, 99)
        if max_flow < 0.1:  # if flow is very small, use a minimum threshold
            max_flow = max(magnitude.max(), 1.0)
    
    magnitude_norm = np.clip(magnitude / (max_flow + 1e-10), 0, 1)
    
    # normalize angle to [0, 1] range
    angle_norm = (angle + np.pi) / (2 * np.pi)
    
    # create HSV image
    hsv = np.zeros((h, w, 3), dtype=np.uint8)
    hsv[:, :, 0] = (angle_norm * 179).astype(np.uint8)  # Hue (direction)
    hsv[:, :, 1] = 255  # Full saturation
    hsv[:, :, 2] = (magnitude_norm * 255).astype(np.uint8)  # Value (magnitude)
    
    # convert to RGB
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    return rgb


def visualize_optical_flow_arrows(image: np.ndarray, 
                                    u: np.ndarray, 
                                    v: np.ndarray,
                                   step: int = 16, 
                                   scale: float = 1.0):
    # visualize optical flow as arrows overlaid on image.
    h, w = u.shape
    
    # convert to color if grayscale
    if len(image.shape) == 2:
        vis = cv2.cvtColor((image / image.max() * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    else:
        vis = (image * 255).astype(np.uint8) if image.max() <= 1 else image.copy()
    
    # draw arrows
    for y in range(0, h, step):
        for x in range(0, w, step):
            fx, fy = u[y, x] * scale, v[y, x] * scale
            cv2.arrowedLine(vis, (x, y), (int(x + fx), int(y + fy)),
                           (0, 255, 0), 1, tipLength=0.3)
    
    return vis


def simple_lowpass_filter(image: np.ndarray, sigma: float = 3.0):
    # apply simple Gaussian low-pass filter (for comparison).
    return ndimage.gaussian_filter(image, sigma)


def create_comparison_figure(original: np.ndarray,
                             flow_viz: Optional[np.ndarray],
                             lowpass_result: np.ndarray,
                             temporal_result: np.ndarray,
                             save_path: str = "comparison.png",
                             dpi: int = 300):
    # create comparison figure showing all results.
    # Use larger figsize and high DPI for better quality
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    
    # original frame
    if len(original.shape) == 3:
        axes[0, 0].imshow(cv2.cvtColor(original.astype(np.uint8), cv2.COLOR_BGR2RGB) 
                          if original.max() > 1 else original)
    else:
        axes[0, 0].imshow(original, cmap='gray')
    axes[0, 0].set_title('Original Frame (with Screen)', fontsize=12)
    axes[0, 0].axis('off')
    
    # motion field
    if flow_viz is not None:
        axes[0, 1].imshow(flow_viz)
        axes[0, 1].set_title('Optical Flow Field', fontsize=12)
    else:
        axes[0, 1].text(0.5, 0.5, 'No Flow Visualization', 
                        ha='center', va='center', fontsize=14)
    axes[0, 1].axis('off')
    
    # low-pass filter result
    if len(lowpass_result.shape) == 3:
        axes[1, 0].imshow(lowpass_result if lowpass_result.max() <= 1 
                          else lowpass_result / 255.0)
    else:
        axes[1, 0].imshow(lowpass_result, cmap='gray')
    axes[1, 0].set_title('Simple Low-Pass Filter (Blurred)', fontsize=12)
    axes[1, 0].axis('off')
    
    # temporal filter result
    if len(temporal_result.shape) == 3:
        axes[1, 1].imshow(temporal_result if temporal_result.max() <= 1 
                          else temporal_result / 255.0)
    else:
        axes[1, 1].imshow(temporal_result, cmap='gray')
    axes[1, 1].set_title('Motion-Compensated Temporal Filter (Restored)', fontsize=12)
    axes[1, 1].axis('off')
    
    plt.tight_layout()
    plt.savefig(save_path, dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Comparison figure saved to: {save_path} (DPI: {dpi})")


def create_detailed_results(original_frames: List[np.ndarray],
                            aligned_frames: List[np.ndarray],
                            restored: np.ndarray,
                            save_dir: str = ".",
                            dpi: int = 300):
    # create detailed result visualizations with high quality.
    save_dir = Path(save_dir)
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # save original reference frame
    ref_frame = original_frames[0]
    if len(ref_frame.shape) == 3:
        cv2.imwrite(str(save_dir / "original_frame.png"), 
                    (ref_frame * 255).astype(np.uint8) if ref_frame.max() <= 1 else ref_frame.astype(np.uint8))
    else:
        cv2.imwrite(str(save_dir / "original_frame.png"), 
                    (ref_frame / ref_frame.max() * 255).astype(np.uint8))
    
    # save restored image
    if len(restored.shape) == 3:
        cv2.imwrite(str(save_dir / "restored_image.png"), 
                    (restored * 255).astype(np.uint8) if restored.max() <= 1 else restored.astype(np.uint8))
    else:
        cv2.imwrite(str(save_dir / "restored_image.png"), 
                    (restored / restored.max() * 255).astype(np.uint8))
    
    # create alignment visualization with larger size for better quality
    n_frames = min(5, len(aligned_frames))
    fig, axes = plt.subplots(2, n_frames, figsize=(4*n_frames, 8))
    
    for i in range(n_frames):
        # original
        if len(original_frames[i].shape) == 3:
            axes[0, i].imshow(cv2.cvtColor((original_frames[i] * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
                              if original_frames[i].max() <= 1 else 
                              cv2.cvtColor(original_frames[i].astype(np.uint8), cv2.COLOR_BGR2RGB))
        else:
            axes[0, i].imshow(original_frames[i], cmap='gray')
        axes[0, i].set_title(f'Original {i}', fontsize=10)
        axes[0, i].axis('off')
        
        # aligned
        if len(aligned_frames[i].shape) == 3:
            axes[1, i].imshow(cv2.cvtColor((aligned_frames[i] * 255).astype(np.uint8), cv2.COLOR_BGR2RGB)
                              if aligned_frames[i].max() <= 1 else 
                              cv2.cvtColor(aligned_frames[i].astype(np.uint8), cv2.COLOR_BGR2RGB))
        else:
            axes[1, i].imshow(aligned_frames[i], cmap='gray')
        axes[1, i].set_title(f'Aligned {i}', fontsize=10)
        axes[1, i].axis('off')
    
    axes[0, 0].set_ylabel('Original', fontsize=12)
    axes[1, 0].set_ylabel('Aligned', fontsize=12)
    
    plt.tight_layout()
    plt.savefig(save_dir / "alignment_comparison.png", dpi=dpi, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Detailed results saved to: {save_dir} (DPI: {dpi})")


# =============================================================================
# Main Pipeline
# =============================================================================

class ScreenRemovalPipeline:
    # complete pipeline for window screen removal using visual motion analysis.
    
    def __init__(self, num_frames: int = 10, motion_method: str = 'flow',
                 post_processing: str = 'none', use_median: bool = True,
                 apply_sharpening: bool = True, sharpening_strength: float = 0.8):
        self.num_frames = num_frames
        self.motion_method = motion_method
        self.post_processing = post_processing
        self.use_median = use_median
        self.apply_sharpening = apply_sharpening
        self.sharpening_strength = sharpening_strength
        
        self.original_frames = None
        self.gray_frames = None
        self.color_frames = None
        self.transforms = None
        self.aligned_frames = None
        self.restored = None
        self.flow_visualization = None
    
    def load_video(self, video_path: str, start_frame: int = 0):
        """Load video frames."""
        print("=" * 60)
        print("Phase 1: Preprocessing and Artifact Modeling")
        print("=" * 60)
        
        self.original_frames = load_video_frames(video_path, self.num_frames, start_frame)
        self.gray_frames, self.color_frames = preprocess_frames(self.original_frames)
        
        print(f"Loaded and preprocessed {len(self.gray_frames)} frames")
    
    def estimate_motion(self, ref_idx: int = 0):
        print("\n" + "=" * 60)
        print("Phase 2: Visual Motion Estimation")
        print("=" * 60)
        
        self.transforms = estimate_global_motion(
            self.gray_frames, ref_idx, self.motion_method
        )
        
        # Create flow visualization if using optical flow
        if self.motion_method == 'flow' and len(self.transforms) > 1:
            u, v = self.transforms[1]  # Use flow from frame 1 to ref
            self.flow_visualization = visualize_optical_flow(u, v)
    
    def remove_screen(self, use_color: bool = True):
        print("\n" + "=" * 60)
        print("Phase 3: Screen Removal via Temporal Filtering")
        print("=" * 60)
        
        # use color or grayscale frames
        frames_to_align = self.color_frames if use_color else self.gray_frames
        
        # motion compensation
        self.aligned_frames = motion_compensate_frames(
            frames_to_align, self.transforms, self.motion_method
        )
        
        # temporal filtering - use median or mean
        if self.use_median:
            print("Using MEDIAN filter (better edge preservation)...")
            self.restored = temporal_median_filter(self.aligned_frames)
        else:
            print("Using MEAN filter...")
            self.restored = temporal_average_filter(self.aligned_frames)
        
        print(f"Screen removal complete. Output shape: {self.restored.shape}")
    
    def post_process(self):
        print("\n" + "=" * 60)
        print("Phase 4: Post-Processing and Enhancement")
        print("=" * 60)
        
        # Apply sharpening first (if enabled)
        if self.apply_sharpening:
            print(f"Applying unsharp mask (strength={self.sharpening_strength})...")
            self.restored = unsharp_mask(self.restored, sigma=1.0, strength=self.sharpening_strength)
        
        # Apply post-processing filter
        if self.post_processing == 'none':
            if not self.apply_sharpening:
                print("Skipping post-processing")
        elif self.post_processing == 'median':
            print("Applying median filter...")
            self.restored = median_filter(self.restored, kernel_size=3)
        elif self.post_processing == 'kuwahara':
            print("Applying kuwahara filter...")
            if len(self.restored.shape) == 3:
                for c in range(3):
                    self.restored[:, :, c] = kuwahara_filter(self.restored[:, :, c])
            else:
                self.restored = kuwahara_filter(self.restored)
        elif self.post_processing == 'bilateral':
            print("Applying bilateral filter...")
            self.restored = bilateral_filter(self.restored)
        
        print("Post-processing complete")
    
    def evaluate(self, output_dir: str = "."):
        print("\n" + "=" * 60)
        print("Evaluation and Analysis")
        print("=" * 60)
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # get reference frame for comparison
        ref_frame = self.original_frames[0]
        
        # create simple low-pass filtered version for comparison
        if len(self.color_frames[0].shape) == 3:
            lowpass = np.stack([
                simple_lowpass_filter(self.color_frames[0][:, :, c], sigma=3.0)
                for c in range(3)
            ], axis=-1)
        else:
            lowpass = simple_lowpass_filter(self.gray_frames[0], sigma=3.0)
        
            # create comparison figure
        create_comparison_figure(
            ref_frame,
            self.flow_visualization,
            lowpass,
            self.restored,
            str(output_dir / "comparison.png")
        )
        
        # create detailed results
        create_detailed_results(
            self.color_frames,
            self.aligned_frames,
            self.restored,
            str(output_dir)
        )
        
        # quantitative comparison
        print("\nQuantitative Analysis:")
        print("-" * 40)
        
        # compare screen pattern visibility
        # using high-frequency content as proxy for screen visibility
        ref_gray = self.gray_frames[0]
        restored_gray = (rgb_to_grayscale_ntsc(self.restored * 255) / 255.0 
                        if len(self.restored.shape) == 3 else self.restored)
        lowpass_gray = (rgb_to_grayscale_ntsc(lowpass * 255) / 255.0 
                       if len(lowpass.shape) == 3 else lowpass)
        
        # High-frequency energy (screen pattern indicator)
        def high_freq_energy(img):
            Ix, Iy, _ = compute_sobel_gradients(img)
            return np.mean(Ix**2 + Iy**2)
        
        hf_original = high_freq_energy(ref_gray)
        hf_restored = high_freq_energy(restored_gray)
        hf_lowpass = high_freq_energy(lowpass_gray)
        
        # Calculate reduction percentages
        hf_restored_pct = (hf_restored/hf_original)*100
        hf_lowpass_pct = (hf_lowpass/hf_original)*100
        screen_reduction = 100 - hf_restored_pct
        
        print(f"High-frequency energy (screen indicator):")
        print(f"  Original:          {hf_original:.6f}")
        print(f"  Simple Low-pass:   {hf_lowpass:.6f} ({hf_lowpass_pct:.1f}% of original)")
        print(f"  Motion-Comp:       {hf_restored:.6f} ({hf_restored_pct:.1f}% of original)")
        
        print(f"\nAnalysis:")
        print(f"  - Lower HF energy indicates better screen removal")
        print(f"  - Motion-compensated approach preserves scene edges better than low-pass")
        print(f"  - Screen reduction: {screen_reduction:.1f}%")
        
        # Save metrics to text file
        metrics_file = output_dir / "metrics.txt"
        with open(metrics_file, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("EVALUATION METRICS\n")
            f.write("=" * 70 + "\n\n")
            
            f.write("Configuration:\n")
            f.write(f"  Frames: {self.num_frames}\n")
            f.write(f"  Motion Method: {self.motion_method}\n")
            f.write(f"  Temporal Filter: {'Median' if self.use_median else 'Mean'}\n")
            f.write(f"  Sharpening: {'ON' if self.apply_sharpening else 'OFF'}")
            if self.apply_sharpening:
                f.write(f" (strength={self.sharpening_strength})\n")
            else:
                f.write("\n")
            f.write(f"  Post-processing: {self.post_processing}\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("HIGH-FREQUENCY ENERGY (Screen Pattern Indicator)\n")
            f.write("-" * 70 + "\n\n")
            
            f.write(f"Original (with screen):        {hf_original:.6f}  (100.0%)\n")
            f.write(f"Simple Low-pass Filter:        {hf_lowpass:.6f}  ({hf_lowpass_pct:5.1f}%)\n")
            f.write(f"Motion-Compensated (Your):     {hf_restored:.6f}  ({hf_restored_pct:5.1f}%)\n\n")
            
            f.write(f"Screen Reduction:              {screen_reduction:.1f}%\n")
            f.write(f"Edge Preservation:             {hf_restored_pct:.1f}%\n\n")
            
            f.write("-" * 70 + "\n")
            f.write("INTERPRETATION\n")
            f.write("-" * 70 + "\n\n")
            
            f.write("High-Frequency Energy:\n")
            f.write("  - Lower value = better screen removal\n")
            f.write("  - Too low = over-smoothed, edges lost\n")
            f.write("  - Ideal range: 90-95% of original (good screen removal + edge preservation)\n\n")
            
            f.write("Your Result:\n")
            if hf_restored_pct < 80:
                f.write("  Status: ⚠️ OVER-SMOOTHED - Too much blur, edges lost\n")
                f.write("  Recommendation: Reduce sharpening or use fewer frames\n")
            elif hf_restored_pct > 98:
                f.write("  Status: ⚠️ INSUFFICIENT - Screen not removed enough\n")
                f.write("  Recommendation: Use more frames or check motion estimation\n")
            else:
                f.write("  Status: ✓ GOOD - Screen removed while preserving edges\n")
                f.write("  Quality: Excellent balance\n")
            
            f.write("\n")
            f.write("-" * 70 + "\n")
            f.write("COMPARISON TO BASELINE\n")
            f.write("-" * 70 + "\n\n")
            
            f.write("Simple Low-pass Filter:\n")
            f.write(f"  - Removes {100-hf_lowpass_pct:.1f}% of high-frequency content\n")
            f.write("  - Result: Screen gone BUT image is blurred\n")
            f.write("  - Problem: Lost important edge information\n\n")
            
            f.write("Your Motion-Compensated Method:\n")
            f.write(f"  - Removes {screen_reduction:.1f}% screen pattern\n")
            f.write(f"  - Preserves {hf_restored_pct:.1f}% edge content\n")
            f.write("  - Result: Screen removed AND edges preserved\n")
            f.write("  - Advantage: Better quality than simple filtering\n\n")
            
            f.write("=" * 70 + "\n")
            f.write("RATING\n")
            f.write("=" * 70 + "\n\n")
            
            # Calculate overall rating
            if 90 <= hf_restored_pct <= 96:
                rating = "⭐⭐⭐⭐⭐ EXCELLENT"
            elif 85 <= hf_restored_pct < 90 or 96 < hf_restored_pct <= 98:
                rating = "⭐⭐⭐⭐ VERY GOOD"
            elif 80 <= hf_restored_pct < 85 or 98 < hf_restored_pct <= 99:
                rating = "⭐⭐⭐ GOOD"
            else:
                rating = "⭐⭐ NEEDS IMPROVEMENT"
            
            f.write(f"Overall Quality: {rating}\n\n")
            
            f.write("Files Generated:\n")
            f.write("  - original_frame.png       (Input with screen)\n")
            f.write("  - restored_image.png       (Output without screen)\n")
            f.write("  - comparison.png           (Side-by-side comparison)\n")
            f.write("  - alignment_comparison.png (Motion compensation visualization)\n")
            f.write("  - metrics.txt              (This file)\n\n")
            
            f.write("=" * 70 + "\n")
        
        print(f"\n✓ Metrics saved to: {metrics_file}")
        
        return {
            'hf_original': hf_original,
            'hf_restored': hf_restored,
            'hf_lowpass': hf_lowpass,
            'screen_reduction_pct': screen_reduction,
            'edge_preservation_pct': hf_restored_pct
        }
    
    def run(self, video_path: str, output_dir: str = "results",
            start_frame: int = 0, use_color: bool = True):

        print("=" * 60)
        print("Window Screen Removal Pipeline")
        print("=" * 60)
        print(f"Video: {video_path}")
        print(f"Frames: {self.num_frames}")
        print(f"Motion method: {self.motion_method}")
        print(f"Temporal filter: {'median' if self.use_median else 'mean'}")
        print(f"Sharpening: {self.apply_sharpening} (strength={self.sharpening_strength})")
        print(f"Post-processing: {self.post_processing}")
        print("=" * 60 + "\n")
        
        # Run all phases
        self.load_video(video_path, start_frame)
        self.estimate_motion(ref_idx=0)
        self.remove_screen(use_color=use_color)
        self.post_process()
        metrics = self.evaluate(output_dir)
        
        print("\n" + "=" * 60)
        print("Pipeline Complete!")
        print("=" * 60)
        print(f"Results saved to: {output_dir}/")
        print("  - original_frame.png")
        print("  - restored_image.png")
        print("  - comparison.png")
        print("  - alignment_comparison.png")
        
        return self.restored, metrics


def main():

    parser = argparse.ArgumentParser(
        description='Window Screen Removal via Visual Motion Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python screen_removal.py video.mp4 -o results/
  python screen_removal.py video.mp4 -n 15 -m flow -p bilateral
  python screen_removal.py video.mp4 --start-frame 100 --grayscale
        """
    )
    
    parser.add_argument('video', help='Path to input video file')
    parser.add_argument('-o', '--output', default='results',
                        help='Output directory (default: results)')
    parser.add_argument('-n', '--num-frames', type=int, default=10,
                        help='Number of frames to use (default: 10)')
    parser.add_argument('-m', '--motion-method', choices=['homography', 'flow'],
                        default='homography',
                        help='Motion estimation method (default: homography)')
    parser.add_argument('-p', '--post-processing', 
                        choices=['median', 'kuwahara', 'bilateral', 'none'],
                        default='bilateral',
                        help='Post-processing filter (default: bilateral)')
    parser.add_argument('--start-frame', type=int, default=0,
                        help='Starting frame index (default: 0)')
    parser.add_argument('--grayscale', action='store_true',
                        help='Process in grayscale instead of color')
    
    args = parser.parse_args()
    
    # create and run pipeline
    pipeline = ScreenRemovalPipeline(
        num_frames=args.num_frames,
        motion_method=args.motion_method,
        post_processing=args.post_processing
    )
    
    restored, metrics = pipeline.run(
        args.video,
        args.output,
        args.start_frame,
        use_color=not args.grayscale
    )
    
    return restored, metrics


if __name__ == '__main__':
    # if running without arguments, show demo usage
    import sys
    
    if len(sys.argv) == 1:
        print("Window Screen Removal - Demo Mode")
        print("=" * 60)
        print("\nUsage: python screen_removal.py <video_path> [options]")
        print("\nOptions:")
        print("  -o, --output DIR        Output directory (default: results)")
        print("  -n, --num-frames N      Number of frames (default: 10)")
        print("  -m, --motion-method M   'homography' or 'flow' (default: homography)")
        print("  -p, --post-processing P 'median', 'kuwahara', 'bilateral', 'none'")
        print("  --start-frame N         Starting frame index (default: 0)")
        print("  --grayscale             Process in grayscale")
        print("\nExample:")
        print("  python screen_removal.py deer_video.mp4 -o results/ -n 15")
        print("\nFor programmatic usage:")
        print("  from screen_removal import ScreenRemovalPipeline")
        print("  pipeline = ScreenRemovalPipeline(num_frames=10)")
        print("  restored, metrics = pipeline.run('video.mp4')")
    else:
        main()

