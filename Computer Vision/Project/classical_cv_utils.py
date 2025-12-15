"""
Classical Computer Vision Utilities

Author: Hasan Suca Kayman
Course: CSc I6716 - Computer Vision
"""

import numpy as np
from scipy import ndimage
from scipy.signal import convolve2d
from typing import Tuple


# =============================================================================
# Image Gradient and Edge Detections
# =============================================================================

def sobel_operator(image: np.ndarray):
    # define Sobel kernels
    sobel_x = np.array([
        [-1, 0, 1],
        [-2, 0, 2],
        [-1, 0, 1]
    ], dtype=np.float64) / 8.0  # normalized
    
    sobel_y = np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1]
    ], dtype=np.float64) / 8.0  # normalized
    
    # convolution
    Gx = convolve2d(image.astype(np.float64), sobel_x, mode='same', boundary='symm')
    Gy = convolve2d(image.astype(np.float64), sobel_y, mode='same', boundary='symm')
    
    # gradient magnitude
    magnitude = np.sqrt(Gx**2 + Gy**2)
    
    return Gx, Gy, magnitude


# NOTE: prewitt_operator not used in demo - commented out
# def prewitt_operator(image: np.ndarray):
#     prewitt_x = np.array([
#         [-1, 0, 1],
#         [-1, 0, 1],
#         [-1, 0, 1]
#     ], dtype=np.float64) / 6.0
#     
#     prewitt_y = np.array([
#         [-1, -1, -1],
#         [ 0,  0,  0],
#         [ 1,  1,  1]
#     ], dtype=np.float64) / 6.0
#     
#     Gx = convolve2d(image.astype(np.float64), prewitt_x, mode='same', boundary='symm')
#     Gy = convolve2d(image.astype(np.float64), prewitt_y, mode='same', boundary='symm')
#     
#     magnitude = np.sqrt(Gx**2 + Gy**2)
#     
#     return Gx, Gy, magnitude


# NOTE: compute_gradient_orientation not used in demo - commented out
# def compute_gradient_orientation(Gx: np.ndarray, Gy: np.ndarray):
#     return np.arctan2(Gy, Gx)


# =============================================================================
# Corner Detection
# =============================================================================

def harris_corner_detector(image: np.ndarray, 
                            k: float = 0.04, 
                           sigma: float = 1.0,
                           threshold_ratio: float = 0.01):
    # compute image gradients
    Ix, Iy, _ = sobel_operator(image)
    
    # compute products of gradients
    Ix2 = Ix * Ix
    Iy2 = Iy * Iy
    Ixy = Ix * Iy
    
    # apply Gaussian window (compute sums in neighborhood)
    Sxx = ndimage.gaussian_filter(Ix2, sigma)
    Syy = ndimage.gaussian_filter(Iy2, sigma)
    Sxy = ndimage.gaussian_filter(Ixy, sigma)
    
    # compute Harris response at each pixel
    # R = det(M) - k * trace(M)**2
    # det(M) = Sxx * Syy - Sxy**2
    # trace(M) = Sxx + Syy
    det_M = Sxx * Syy - Sxy * Sxy
    trace_M = Sxx + Syy
    R = det_M - k * (trace_M ** 2)
    
    # threshold and find corners
    threshold = threshold_ratio * R.max()
    corners = np.argwhere(R > threshold)
    
    return corners, R


# NOTE: shi_tomasi_corners not used in demo - commented out
# def shi_tomasi_corners(image: np.ndarray, 
#                         sigma: float = 1.0,
#                        threshold_ratio: float = 0.01):
# 
#     Ix, Iy, _ = sobel_operator(image)
#     
#     Sxx = ndimage.gaussian_filter(Ix * Ix, sigma)
#     Syy = ndimage.gaussian_filter(Iy * Iy, sigma)
#     Sxy = ndimage.gaussian_filter(Ix * Iy, sigma)
#     
#     # compute minimum eigenvalue analytically
#     # for 2x2 symmetric matrix, eigenvalues are
#     # lambda = (trace +- sqrt(trace**2 - 4*det)) / 2
#     trace_M = Sxx + Syy
#     det_M = Sxx * Syy - Sxy * Sxy
#     
#     # discriminant
#     disc = np.sqrt(np.maximum(trace_M**2 - 4*det_M, 0))
#     
#     # minimum eigenvalue
#     min_eigenvalue = (trace_M - disc) / 2
#     
#     # threshold
#     threshold = threshold_ratio * min_eigenvalue.max()
#     corners = np.argwhere(min_eigenvalue > threshold)
#     
#     return corners, min_eigenvalue


# NOTE: non_maximum_suppression not used in demo - commented out
# def non_maximum_suppression(corners: np.ndarray, 
#                             response: np.ndarray,
#                             image_shape: Tuple[int, int],
#                             window_size: int = 10):
# 
#     if len(corners) == 0:
#         return corners
#     
#     h, w = image_shape
#     suppressed = np.zeros(image_shape, dtype=bool)
#     
#     # sort corners by response value (descending)
#     responses = response[corners[:, 0], corners[:, 1]]
#     sorted_indices = np.argsort(-responses)
#     
#     selected_corners = []
#     
#     for idx in sorted_indices:
#         y, x = corners[idx]
#         
#         # check if this corner is suppressed
#         if suppressed[y, x]:
#             continue
#         
#         selected_corners.append([y, x])
#         
#         # suppress nearby corners
#         y_min = max(0, y - window_size // 2)
#         y_max = min(h, y + window_size // 2 + 1)
#         x_min = max(0, x - window_size // 2)
#         x_max = min(w, x + window_size // 2 + 1)
#         
#         suppressed[y_min:y_max, x_min:x_max] = True
#     
#     return np.array(selected_corners)


# =============================================================================
# Optical Flow
# =============================================================================

# NOTE: lucas_kanade_flow not used in demo - we use OpenCV's implementation
# def lucas_kanade_flow(frame1: np.ndarray, 
#                         frame2: np.ndarray,
#                         window_size: int = 15,
#                         eigenvalue_threshold: float = 1e-4):
# 
#     # ensure float64
#     I1 = frame1.astype(np.float64)
#     I2 = frame2.astype(np.float64)
#     
#     h, w = I1.shape
#     half_win = window_size // 2
#     
#     # compute spatial gradients (on first frame)
#     Ix, Iy, _ = sobel_operator(I1)
#     
#     # compute temporal gradient
#     It = I2 - I1
#     
#     # initialize flow fields
#     u = np.zeros((h, w), dtype=np.float64)
#     v = np.zeros((h, w), dtype=np.float64)
#     
#     # process each pixel
#     for y in range(half_win, h - half_win):
#         for x in range(half_win, w - half_win):
#             # extract local windows
#             Ix_win = Ix[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             Iy_win = Iy[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             It_win = It[y-half_win:y+half_win+1, x-half_win:x+half_win+1].flatten()
#             
#             # build A matrix and b vector
#             A = np.column_stack([Ix_win, Iy_win])
#             b = -It_win
#             
#             # compute A^TA (structure tensor at this point)
#             ATA = A.T @ A
#             
#             # check conditioning using eigenvalues
#             eigenvalues = np.linalg.eigvalsh(ATA)
#             
#             if eigenvalues.min() > eigenvalue_threshold:
#                 # solve normal equations
#                 ATb = A.T @ b
#                 flow = np.linalg.solve(ATA, ATb)
#                 u[y, x] = flow[0]
#                 v[y, x] = flow[1]
#     
#     return u, v


# NOTE: horn_schunck_flow not used in demo - commented out
# def horn_schunck_flow(frame1: np.ndarray, frame2: np.ndarray,
#                       alpha: float = 1.0, num_iterations: int = 100,
#                       convergence_threshold: float = 1e-4):
# 
#     I1 = frame1.astype(np.float64)
#     I2 = frame2.astype(np.float64)
#     
#     h, w = I1.shape
#     
#     # compute gradieentst
#     Ix, Iy, _ = sobel_operator(I1)
#     It = I2 - I1
#     
#     # initialize flow
#     u = np.zeros((h, w), dtype=np.float64)
#     v = np.zeros((h, w), dtype=np.float64)
#     
#     # averaging kernel for Laplacian approximation
#     kernel = np.array([
#         [0, 1/4, 0],
#         [1/4, 0, 1/4],
#         [0, 1/4, 0]
#     ], dtype=np.float64)
#     
#     # precompute denominator
#     denom = alpha**2 + Ix**2 + Iy**2
#     
#     # Iterate
#     for iteration in range(num_iterations):
#         # compute local averages
#         u_avg = convolve2d(u, kernel, mode='same', boundary='symm')
#         v_avg = convolve2d(v, kernel, mode='same', boundary='symm')
#         
#         # update equations (from Euler-Lagrange)
#         common = (Ix * u_avg + Iy * v_avg + It) / denom
#         u_new = u_avg - Ix * common
#         v_new = v_avg - Iy * common
#         
#         # check convergence
#         change = np.mean((u_new - u)**2 + (v_new - v)**2)
#         if change < convergence_threshold:
#             break
#         
#         u = u_new
#         v = v_new
#     
#     return u, v


# NOTE: pyramidal_lucas_kanade not used in demo - we use OpenCV's implementation
# def pyramidal_lucas_kanade(frame1: np.ndarray, frame2: np.ndarray,
#                            num_levels: int = 3,
#                            window_size: int = 15):
#     # build image pyramids
#     pyramid1 = [frame1.astype(np.float64)]
#     pyramid2 = [frame2.astype(np.float64)]
#     
#     for level in range(1, num_levels):
#         # downsample by factor of 2 :)
#         prev1 = pyramid1[-1]
#         prev2 = pyramid2[-1]
#         
#         # gaussian blur before downsampling
#         blurred1 = ndimage.gaussian_filter(prev1, 1.0)
#         blurred2 = ndimage.gaussian_filter(prev2, 1.0)
#         
#         # subsample
#         downsampled1 = blurred1[::2, ::2]
#         downsampled2 = blurred2[::2, ::2]
#         
#         pyramid1.append(downsampled1)
#         pyramid2.append(downsampled2)
#     
#     # start from coarsest level
#     coarsest1 = pyramid1[-1]
#     coarsest2 = pyramid2[-1]
#     
#     u, v = lucas_kanade_flow(coarsest1, coarsest2, window_size)
#     
#     # propagate to finer levels
#     for level in range(num_levels - 2, -1, -1):
#         # upsample flow
#         new_h, new_w = pyramid1[level].shape
#         
#         # scale flow values by 2
#         u = 2 * ndimage.zoom(u, 2, order=1)[:new_h, :new_w]
#         v = 2 * ndimage.zoom(v, 2, order=1)[:new_h, :new_w]
#         
#         # warp frame2 using current flow estimate
#         y_coords, x_coords = np.mgrid[0:new_h, 0:new_w]
#         warped_x = x_coords + u
#         warped_y = y_coords + v
#         
#         # bilinear interpolation for warping
#         warped2 = ndimage.map_coordinates(
#             pyramid2[level], [warped_y, warped_x], order=1, mode='reflect'
#         )
#         
#         # compute residual flow
#         du, dv = lucas_kanade_flow(pyramid1[level], warped2, window_size)
#         
#         # add residual to current estimate
#         u = u + du
#         v = v + dv
#     
#     return u, v


# =============================================================================
# Homography Estimation
# =============================================================================

# NOTE: direct_linear_transform not used in demo - we use cv2.findHomography
# def direct_linear_transform(src_pts: np.ndarray, dst_pts: np.ndarray):
#     n = len(src_pts)
#     
#     # normalize points for numerical stability
#     src_centered = src_pts - src_pts.mean(axis=0)
#     src_scale = np.sqrt(2) / np.std(src_centered)
#     src_norm = src_centered * src_scale
#     
#     dst_centered = dst_pts - dst_pts.mean(axis=0)
#     dst_scale = np.sqrt(2) / np.std(dst_centered)
#     dst_norm = dst_centered * dst_scale
#     
#     # normalization matrices
#     T_src = np.array([
#         [src_scale, 0, -src_scale * src_pts.mean(axis=0)[0]],
#         [0, src_scale, -src_scale * src_pts.mean(axis=0)[1]],
#         [0, 0, 1]
#     ])
#     
#     T_dst = np.array([
#         [dst_scale, 0, -dst_scale * dst_pts.mean(axis=0)[0]],
#         [0, dst_scale, -dst_scale * dst_pts.mean(axis=0)[1]],
#         [0, 0, 1]
#     ])
#     
#     # build design matrix A
#     A = []
#     for i in range(n):
#         x, y = src_norm[i]
#         xp, yp = dst_norm[i]
#         
#         A.append([-x, -y, -1, 0, 0, 0, x*xp, y*xp, xp])
#         A.append([0, 0, 0, -x, -y, -1, x*yp, y*yp, yp])
#     
#     A = np.array(A)
#     
#     # solve using SVD
#     U, S, Vh = np.linalg.svd(A)
#     
#     # solution is last row of Vh (corresponding to smallest singular value)
#     h = Vh[-1]
#     H_norm = h.reshape(3, 3)
#     
#     # denormalize
#     H = np.linalg.inv(T_dst) @ H_norm @ T_src
#     H = H / H[2, 2]  # normalize so H[2,2] = 1
#     
#     return H


# NOTE: ransac_homography not used in demo - we use cv2.findHomography
# def ransac_homography(src_pts: np.ndarray, dst_pts: np.ndarray,
#                       num_iterations: int = 1000,
#                       threshold: float = 5.0,
#                       min_inliers: int = 4):
# 
#     n = len(src_pts)
#     
#     if n < 4:
#         return np.eye(3), np.zeros(n, dtype=bool)
#     
#     best_H = np.eye(3)
#     best_inliers = np.zeros(n, dtype=bool)
#     best_num_inliers = 0
#     
#     for _ in range(num_iterations):
#         # random sample of 4 points
#         indices = np.random.choice(n, 4, replace=False)
#         
#         src_sample = src_pts[indices]
#         dst_sample = dst_pts[indices]
#         
#         # check for degenerate configuration (collinear points)
#         if is_degenerate(src_sample) or is_degenerate(dst_sample):
#             continue
#         
#         try:
#             H = direct_linear_transform(src_sample, dst_sample)
#         except:
#             continue
#         
#         # project all source points
#         src_homo = np.hstack([src_pts, np.ones((n, 1))])
#         projected = (H @ src_homo.T).T
#         projected = projected[:, :2] / projected[:, 2:3]
#         
#         # compute errors
#         errors = np.linalg.norm(projected - dst_pts, axis=1)
#         
#         # find inliers
#         inliers = errors < threshold
#         num_inliers = np.sum(inliers)
#         
#         if num_inliers > best_num_inliers:
#             best_num_inliers = num_inliers
#             best_inliers = inliers
#             best_H = H
#     
#     # refine using all inliers
#     if best_num_inliers >= min_inliers:
#         best_H = direct_linear_transform(src_pts[best_inliers], dst_pts[best_inliers])
#     
#     return best_H, best_inliers


# NOTE: is_degenerate not used in demo - commented out
# def is_degenerate(points: np.ndarray, threshold: float = 1e-6):
# 
#     if len(points) < 3:
#         return True
#     
#     # check area of triangle formed by first 3 points
#     p0, p1, p2 = points[:3]
#     area = 0.5 * abs((p1[0] - p0[0]) * (p2[1] - p0[1]) - 
#                      (p2[0] - p0[0]) * (p1[1] - p0[1]))
#     
#     return area < threshold


# =============================================================================
# Filtering Operations
# =============================================================================

# NOTE: gaussian_filter_2d not used - we use scipy.ndimage.gaussian_filter
# def gaussian_filter_2d(image: np.ndarray, sigma: float):
# 
#     # determine kernel size
#     size = int(6 * sigma + 1)
#     if size % 2 == 0:
#         size += 1
#     
#     # create 1D Gaussian kernel
#     x = np.arange(size) - size // 2
#     kernel_1d = np.exp(-x**2 / (2 * sigma**2))
#     kernel_1d = kernel_1d / kernel_1d.sum()
#     
#     # apply separable convolution
#     result = convolve2d(image, kernel_1d.reshape(1, -1), mode='same', boundary='symm')
#     result = convolve2d(result, kernel_1d.reshape(-1, 1), mode='same', boundary='symm')
#     
#     return result


# NOTE: box_filter_2d not used in demo - commented out
# def box_filter_2d(image: np.ndarray, size: int):
# 
#     kernel = np.ones((size, size), dtype=np.float64) / (size * size)
#     return convolve2d(image, kernel, mode='same', boundary='symm')


# NOTE: laplacian_of_gaussian not used in demo - commented out
# def laplacian_of_gaussian(image: np.ndarray, sigma: float):
# 
#     # first smooth
#     smoothed = gaussian_filter_2d(image, sigma)
#     
#     # then apply Laplacian CHECK THE VALUES OF THE MATRIX DONT FORGET TO CHANGE THEM
#     laplacian = np.array([
#         [0,  1, 0],
#         [1, -4, 1],
#         [0,  1, 0]
#     ], dtype=np.float64)
#     
#     return convolve2d(smoothed, laplacian, mode='same', boundary='symm')


# =============================================================================
# Frequency Domain Analysis
# =============================================================================

def analyze_frequency_spectrum(image: np.ndarray):
    # compute 2D FFT
    fft = np.fft.fft2(image)
    
    # shift zero frequency to center
    fft_shifted = np.fft.fftshift(fft)
    
    # magnitude and phase
    magnitude = np.abs(fft_shifted)
    phase = np.angle(fft_shifted)
    
    # log scale for better visualization
    magnitude_log = np.log1p(magnitude)
    
    return magnitude_log, phase


def detect_periodic_pattern(image: np.ndarray, 
                            min_period: int = 3,
                            max_period: int = 30):

    h, w = image.shape
    
    # compute FFT
    fft = np.fft.fft2(image)
    magnitude = np.abs(np.fft.fftshift(fft))
    
    # find peaks (excluding DC component)
    center_y, center_x = h // 2, w // 2
    
    # zero out DC and low frequencies
    magnitude[center_y-2:center_y+3, center_x-2:center_x+3] = 0
    
    # find frequency corresponding to period range
    min_freq = 1 / max_period
    max_freq = 1 / min_period
    
    # convert to FFT indices
    min_idx_y = int(min_freq * h)
    max_idx_y = int(max_freq * h)
    min_idx_x = int(min_freq * w)
    max_idx_x = int(max_freq * w)
    
    # search for peaks in valid range
    # vertical pattern
    horiz_slice = magnitude[center_y, center_x+min_idx_x:center_x+max_idx_x]
    if len(horiz_slice) > 0 and horiz_slice.max() > magnitude.mean() * 5:
        peak_idx_x = np.argmax(horiz_slice) + min_idx_x
        period_x = w / peak_idx_x
    else:
        period_x = None
    
    # horizontal pattern
    vert_slice = magnitude[center_y+min_idx_y:center_y+max_idx_y, center_x]
    if len(vert_slice) > 0 and vert_slice.max() > magnitude.mean() * 5:
        peak_idx_y = np.argmax(vert_slice) + min_idx_y
        period_y = h / peak_idx_y
    else:
        period_y = None
    
    if period_x is not None or period_y is not None:
        return (period_x or 0, period_y or 0)
    
    return None
