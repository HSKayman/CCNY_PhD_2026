# %%
"""
STEREO VISION SYSTEM - HW4
===========================

This program implements a complete stereo vision system with the following features:

PART 1: FUNDAMENTAL MATRIX ESTIMATION (15 points)
- Normalized 8-point algorithm for robust F matrix computation
- SVD-based epipole computation from F matrix
- Accuracy verification using test points not used in estimation
- Visualization of epipolar lines for both control and test points

PART 2: FEATURE-BASED MATCHING (15 points)
- Interactive GUI for point selection
- Sum of Squared Differences (SSD) matching algorithm
- Epipolar constraint for efficient search
- Automatic match finding with visual feedback

PART 3: ANALYSIS & DISCUSSION (10 points)
- Region type analysis (corners, edges, smooth, textured)
- Automatic vs manual matching comparison
- Performance analysis on different region types
- Discussion of success/failure cases

FEATURES:
- Manual calibration with at least 8 point pairs (auto-compute at 10 points)
- Automatic feature matching along epipolar lines
- Region characterization (variance, gradients)
- Manual vs automatic matching comparison mode
- Comprehensive visualization and reporting

USAGE:
1. Click corresponding points on left and right images (at least 8 pairs)
2. System auto-computes F matrix after 10 points (or press 'c' after 8)
3. Click on left image to find automatic matches
4. Press 'm' to compare automatic vs manual matching
5. Press 'r' for detailed report
6. Press 'e' to view epipolar lines overlay

ALGORITHM DETAILS:
- Feature: Raw intensity values in 15x15 window
- Matching: SSD along epipolar line
- Constraint: Epipolar geometry from F matrix
- Effectiveness: Good for textured regions, poor for smooth/repetitive areas
"""

#!pip install opencv-python numpy

# %%
import cv2
import numpy as np
import math

# %%
global img1, img2, img_combined, img_display, test_mode, F_matrix, manual_match_mode, manual_match_point
ref_points_1 = [] # Left image points
ref_points_2 = [] # Right image points
test_mode = False
manual_match_mode = False  # For comparing automatic vs manual matching
manual_match_point = None  # Store manual clicked match
img_display = None  # Current display image (with markers)

# %% [markdown]
# # ==========================================
# # PART 1: FUNDAMENTAL MATRIX & EPIPOLES
# # ==========================================

# %%
def normalize_points(pts, width, height):
    """
    Normalizes points to improve 8-point algorithm stability.
    Translate centroid to origin and scale so average distance is sqrt(2).
    """
    pts = np.array(pts)
    centroid = np.mean(pts, axis=0)
    
    # Shift origin to centroid
    shifted_pts = pts - centroid
    
    # Calculate average distance from origin
    mean_dist = np.mean(np.sqrt(np.sum(shifted_pts**2, axis=1)))
    
    # Scale factor
    scale = np.sqrt(2) / mean_dist
    
    # Construct transformation matrix T
    T = np.array([
        [scale, 0, -scale * centroid[0]],
        [0, scale, -scale * centroid[1]],
        [0, 0, 1]
    ])
    
    # Apply T to points (convert to homogeneous coords first)
    pts_h = np.column_stack((pts, np.ones(len(pts))))
    pts_norm = (T @ pts_h.T).T
    
    return pts_norm[:, :2], T

# %%
def compute_fundamental_matrix(pts1, pts2):
    """
    Computes F using the normalized 8-point algorithm.
    Reference: Stereo Vision Slides, Page 32.
    """
    h, w = 1000, 1000 # Arbitrary for normalization, just need image dims
    
    # 1. Normalize points
    pts1_norm, T1 = normalize_points(pts1, w, h)
    pts2_norm, T2 = normalize_points(pts2, w, h)
    
    # 2. Build Constraint Matrix A
    # Equation: p2' * F * p1 = 0 -> [u'u, u'v, u', v'u, v'v, v', u, v, 1] * f = 0
    A = []
    for i in range(len(pts1)):
        u, v = pts1_norm[i]
        u_p, v_p = pts2_norm[i]
        A.append([u_p*u, u_p*v, u_p, v_p*u, v_p*v, v_p, u, v, 1])
    A = np.array(A)
    
    # 3. SVD of A to find F
    U, S, Vt = np.linalg.svd(A)
    F_prime = Vt[-1].reshape(3, 3)
    
    # 4. Enforce Rank 2 Constraint (Singularity constraint)
    # Reference: Stereo Vision Slides, Page 32 ("Set smallest singular value to 0")
    Uf, Sf, Vtf = np.linalg.svd(F_prime)
    Sf[2] = 0 # Zero out smallest singular value
    F_rank2 = Uf @ np.diag(Sf) @ Vtf
    
    # 5. De-normalize: F = T2' * F_rank2 * T1
    F = T2.T @ F_rank2 @ T1
    
    # Normalize F so last element is 1 (standard convention)
    return F / F[2, 2]

# %%
def compute_epipoles(F):
    """
    Computes epipoles using SVD.
    Reference: Stereo Vision Slides, Page 33.
    """
    # Epipole e1 (left) is null space of F: F * e1 = 0
    U, S, Vt = np.linalg.svd(F)
    e1 = Vt[-1]
    e1 = e1 / e1[2] # Normalize
    
    # Epipole e2 (right) is null space of F.T: F.T * e2 = 0
    U, S, Vt = np.linalg.svd(F.T)
    e2 = Vt[-1]
    e2 = e2 / e2[2] # Normalize
    
    return e1, e2

# %%
def compute_epipolar_line(pt, F, which_image):
    """
    Computes the line equation ax + by + c = 0.
    If pt is in image 1, line is in image 2: l' = F * p
    If pt is in image 2, line is in image 1: l = F.T * p'
    """
    pt_h = np.array([pt[0], pt[1], 1])
    
    if which_image == 1: # Point in Img1, line in Img2
        line = F @ pt_h
    else: # Point in Img2, line in Img1
        line = F.T @ pt_h
        
    return line

# %%
def calculate_distance_to_line(pt, line):
    """ Calculates geometric distance from point (x,y) to line ax+by+c=0 """
    a, b, c = line
    x, y = pt
    return abs(a*x + b*y + c) / math.sqrt(a**2 + b**2)

# %% [markdown]
# # ==========================================
# # PART 2: FEATURE MATCHING & GUI
# # ==========================================

# %%
def analyze_region_type(img, pt, window_size=15):
    """
    Analyzes the type of region around a point.
    Returns: region type and characteristics for discussion.
    """
    h, w = img.shape[:2]
    x, y = pt
    half_w = window_size // 2
    
    if x < half_w or x >= w - half_w or y < half_w or y >= h - half_w:
        return "BORDER", {}
    
    # Extract window
    window = img[y-half_w:y+half_w+1, x-half_w:x+half_w+1]
    gray_window = cv2.cvtColor(window, cv2.COLOR_BGR2GRAY) if len(window.shape) == 3 else window
    
    # Calculate statistics
    variance = np.var(gray_window)
    std_dev = np.std(gray_window)
    
    # Calculate gradients (for edge/corner detection)
    sobel_x = cv2.Sobel(gray_window, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray_window, cv2.CV_64F, 0, 1, ksize=3)
    gradient_mag = np.sqrt(sobel_x**2 + sobel_y**2)
    avg_gradient = np.mean(gradient_mag)
    
    # Harris corner response (simplified)
    Ix2 = sobel_x ** 2
    Iy2 = sobel_y ** 2
    Ixy = sobel_x * sobel_y
    
    # Classify region
    region_type = ""
    if variance < 100:
        region_type = "SMOOTH (Low texture)"
    elif avg_gradient > 50:
        # Check if corner or edge
        det = (Ix2.mean() * Iy2.mean()) - (Ixy.mean() ** 2)
        trace = Ix2.mean() + Iy2.mean()
        if det > 0.01 * (trace ** 2):
            region_type = "CORNER (High texture, directional change)"
        else:
            region_type = "EDGE (Strong gradient)"
    else:
        region_type = "TEXTURED (Moderate variation)"
    
    stats = {
        'variance': variance,
        'std_dev': std_dev,
        'avg_gradient': avg_gradient,
        'type': region_type
    }
    
    return region_type, stats

# %% [markdown]
# # ==========================================
# # PART 2: FEATURE MATCHING & GUI
# # ==========================================

# %%
def match_feature_along_line(img1, img2, pt_clicked, F, window_size=15):
    """
    Searches for the corresponding point in img2 along the epipolar line.
    Uses Sum of Squared Differences (SSD).
    Reference: "Correspondence Problem", Slides 41-45.
    """
    h, w, _ = img2.shape
    
    # 1. Get Epipolar Line in Image 2
    line = compute_epipolar_line(pt_clicked, F, 1) # a*x + b*y + c = 0
    a, b, c = line
    
    # 2. Extract template from Image 1
    x, y = pt_clicked
    half_w = window_size // 2
    
    # Check bounds
    if x < half_w or x >= w - half_w or y < half_w or y >= h - half_w:
        print("Point too close to border.")
        return None

    template = img1[y-half_w:y+half_w+1, x-half_w:x+half_w+1].astype(np.float32)
    
    # 3. Scan along the epipolar line in Image 2
    best_score = float('inf')
    best_pt = None
    
    # We iterate x from 0 to width (assuming line isn't vertical)
    # Ideally we should trace the line pixels properly (Bresenham or similar)
    # Simple approximation: calculate y for every x
    
    for x2 in range(half_w, w - half_w):
        # Calculate y on the line: y = (-c - ax) / b
        if abs(b) > 1e-5:
            y2 = int((-c - a * x2) / b)
        else:
            continue # Vertical line handling skipped for brevity
            
        if y2 < half_w or y2 >= h - half_w:
            continue
            
        # Extract window in Image 2
        patch = img2[y2-half_w:y2+half_w+1, x2-half_w:x2+half_w+1].astype(np.float32)
        
        # Compute SSD (Sum of Squared Differences)
        score = np.sum((template - patch)**2)
        
        if score < best_score:
            best_score = score
            best_pt = (x2, y2)
            
    return best_pt

# %%
def mouse_callback(event, x, y, flags, param):
    global ref_points_1, ref_points_2, test_mode, F_matrix, img1, img2, img_combined, img_display
    global manual_match_mode, manual_match_point
    
    if event == cv2.EVENT_LBUTTONDOWN:
        if not test_mode:
            # Calibration Phase: Collect pairs
            w = img1.shape[1]
            
            if len(ref_points_1) == len(ref_points_2):
                # It's time to click on LEFT image
                if x >= w:
                    print("❌ Please click on the LEFT image first!")
                    return
                    
                ref_points_1.append((x, y))
                print(f"✓ Point {len(ref_points_1)} on Left Image recorded: ({x},{y}). Now click corresponding point on Right.")
                cv2.circle(img_combined, (x, y), 5, (0, 0, 255), -1)
            else:
                # It's time to click on RIGHT image
                if x < w:
                    print("❌ Please click on the RIGHT image now!")
                    return
                    
                # Adjust x for the right image (displayed side-by-side)
                real_x = x - w
                ref_points_2.append((real_x, y))
                print(f"✓ Point {len(ref_points_2)} on Right Image recorded: ({real_x},{y}).")
                cv2.circle(img_combined, (x, y), 5, (0, 255, 0), -1)
                
                if len(ref_points_1) >= 18:
                    print("--- 18 Points collected. Press 'c' to Compute F or click more for better accuracy ---")
                
                # Auto-calculate after 10 points
                if len(ref_points_1) == 10:
                    print("\n🎯 10 Points collected! Auto-calculating Fundamental Matrix...")
                    compute_and_display_results()

            cv2.imshow("Stereo Lab", img_combined)
            
        else:
            # Testing Phase: Feature Matching or Manual Comparison
            w = img1.shape[1]
            
            # Check if we're waiting for manual match input
            if manual_match_mode and manual_match_point is not None:
                # User is clicking the manual match on the right image
                if x >= w:
                    real_x = x - w
                    manual_pt = (real_x, y)
                    auto_pt = manual_match_point['auto_match']
                    clicked_pt = manual_match_point['clicked']
                    
                    # Calculate distances
                    dist_auto = math.sqrt((auto_pt[0] - real_x)**2 + (auto_pt[1] - y)**2)
                    
                    print(f"\n=== MANUAL vs AUTOMATIC COMPARISON ===")
                    print(f"Left Point: {clicked_pt}")
                    print(f"Automatic Match: {auto_pt}")
                    print(f"Your Manual Match: {manual_pt}")
                    print(f"Distance between Auto and Manual: {dist_auto:.2f} pixels")
                    
                    # Draw comparison
                    img_show = img_combined.copy()
                    
                    # Draw clicked point
                    cv2.circle(img_show, clicked_pt, 10, (255, 0, 0), 2)
                    
                    # Draw automatic match (GREEN)
                    auto_display = (auto_pt[0] + w, auto_pt[1])
                    cv2.circle(img_show, auto_display, 10, (0, 255, 0), 2)
                    cv2.putText(img_show, "AUTO", (auto_display[0]+12, auto_display[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # Draw manual match (CYAN)
                    manual_display = (manual_pt[0] + w, manual_pt[1])
                    cv2.circle(img_show, manual_display, 10, (255, 255, 0), 2)
                    cv2.putText(img_show, "MANUAL", (manual_display[0]+12, manual_display[1]), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
                    
                    # Draw epipolar line
                    line = compute_epipolar_line(clicked_pt, F_matrix, 1)
                    x0, y0 = 0, int(-line[2]/line[1])
                    x1, y1 = img2.shape[1], int(-(line[2] + line[0]*img2.shape[1])/line[1])
                    cv2.line(img_show, (x0 + w, y0), (x1 + w, y1), (0, 255, 255), 1)
                    
                    # Add text
                    text = f"Auto vs Manual: {dist_auto:.1f}px difference"
                    cv2.putText(img_show, text, (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    
                    img_display = img_show
                    cv2.imshow("Stereo Lab", img_display)
                    
                    manual_match_mode = False
                    manual_match_point = None
                    print("Press 'm' on a new point to compare again, or continue normal matching.")
                else:
                    print("Please click on the RIGHT image for manual match.")
                return
            
            if x < w: # Clicked on Left Image
                print(f"\n🔍 Searching match for LEFT point: ({x}, {y})...")
                
                # Analyze region type
                region_type, stats = analyze_region_type(img1, (x, y))
                print(f"📊 Region Analysis: {region_type}")
                print(f"   Variance: {stats['variance']:.2f}, Gradient: {stats['avg_gradient']:.2f}")
                
                # Start with clean image
                img_show = img_combined.copy()
                
                # Find match
                match_pt = match_feature_along_line(img1, img2, (x,y), F_matrix)
                
                if match_pt:
                    mx, my = match_pt
                    print(f"✅ Match found at RIGHT point: ({mx}, {my})")
                    print(f"📍 Matched Coordinates: LEFT({x}, {y}) ↔ RIGHT({mx}, {my})")
                    
                    # Store for manual comparison if 'm' key was pressed
                    if manual_match_mode:
                        manual_match_point = {
                            'clicked': (x, y),
                            'auto_match': (mx, my)
                        }
                        print("\n🔵 Now click on the RIGHT image where YOU think the match is...")
                        print("   (This allows comparison between automatic and manual matching)")
                    
                    # Offset for visualization (right image starts at w)
                    w = img1.shape[1]
                    
                    # Draw Epipolar Line on Right Image (YELLOW)
                    line = compute_epipolar_line((x,y), F_matrix, 1)
                    x0, y0 = 0, int(-line[2]/line[1])
                    x1, y1 = img2.shape[1], int(-(line[2] + line[0]*img2.shape[1])/line[1])
                    cv2.line(img_show, (x0 + w, y0), (x1 + w, y1), (0, 255, 255), 2)
                    
                    # Draw connecting line between matched points (MAGENTA)
                    mx_display = mx + w
                    cv2.line(img_show, (x, y), (mx_display, my), (255, 0, 255), 3)
                    
                    # ===== Draw LEFT point (BLUE with WHITE border) =====
                    cv2.circle(img_show, (x, y), 15, (255, 0, 0), -1)  # Blue filled
                    cv2.circle(img_show, (x, y), 17, (255, 255, 255), 3)  # White border
                    cv2.circle(img_show, (x, y), 3, (255, 255, 255), -1)  # White center dot
                    
                    # ===== Draw RIGHT matched point (BRIGHT GREEN with WHITE border) =====
                    cv2.circle(img_show, (mx_display, my), 15, (0, 255, 0), -1)  # Green filled
                    cv2.circle(img_show, (mx_display, my), 17, (255, 255, 255), 3)  # White border
                    cv2.circle(img_show, (mx_display, my), 3, (255, 255, 255), -1)  # White center dot
                    
                    # Add crosshair on matched point for extra visibility
                    cv2.drawMarker(img_show, (mx_display, my), (0, 0, 255), 
                                  cv2.MARKER_CROSS, 30, 3)  # RED crosshair
                    
                    # ===== DISPLAY MATCHED COORDINATES ON IMAGE =====
                    # Create a semi-transparent overlay for text background
                    overlay = img_show.copy()
                    
                    # Add coordinate text box at the top
                    text1 = f"LEFT ({x}, {y})  <-->  RIGHT ({mx}, {my})"
                    text2 = f"Region: {region_type}"
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 0.6
                    thickness = 2
                    
                    # Get text sizes
                    (text1_width, text1_height), baseline1 = cv2.getTextSize(text1, font, font_scale, thickness)
                    (text2_width, text2_height), baseline2 = cv2.getTextSize(text2, font, 0.5, 1)
                    
                    # Position at top center
                    text1_x = (img_show.shape[1] - text1_width) // 2
                    text1_y = 30
                    text2_x = (img_show.shape[1] - text2_width) // 2
                    text2_y = text1_y + text1_height + 15
                    
                    # Draw background rectangle
                    cv2.rectangle(overlay, 
                                (text1_x - 10, text1_y - text1_height - 8),
                                (text2_x + text2_width + 10, text2_y + baseline2 + 5),
                                (0, 0, 0), -1)
                    
                    # Blend overlay with original
                    cv2.addWeighted(overlay, 0.7, img_show, 0.3, 0, img_show)
                    
                    # Draw the texts
                    cv2.putText(img_show, text1, (text1_x, text1_y),
                               font, font_scale, (0, 255, 255), thickness, cv2.LINE_AA)
                    cv2.putText(img_show, text2, (text2_x, text2_y),
                               font, 0.5, (255, 255, 0), 1, cv2.LINE_AA)
                    
                    # Store and display the marked image
                    img_display = img_show
                    cv2.imshow("Stereo Lab", img_display)
                else:
                    print("❌ Match not found (out of bounds).")
                    img_display = img_show
                    cv2.imshow("Stereo Lab", img_display)
            else:
                print("⚠️ Please click on the LEFT image to find matches.")

# %%
def draw_epipolar_lines_overlay(img1, img2, pts1, pts2, F, line_color=(0, 255, 0)):
    """
    Draws epipolar lines for all point correspondences on both images.
    Returns images with overlaid epipolar lines.
    """
    img1_lines = img1.copy()
    img2_lines = img2.copy()
    h, w = img2.shape[:2]
    
    for i, (pt1, pt2) in enumerate(zip(pts1, pts2)):
        # Draw point on left image
        cv2.circle(img1_lines, pt1, 4, (0, 0, 255), -1)
        cv2.putText(img1_lines, str(i+1), (pt1[0]+8, pt1[1]-8), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw point on right image
        cv2.circle(img2_lines, pt2, 4, (0, 255, 0), -1)
        cv2.putText(img2_lines, str(i+1), (pt2[0]+8, pt2[1]-8), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Draw epipolar line on right image (for left point)
        line = compute_epipolar_line(pt1, F, 1)
        a, b, c = line
        if abs(b) > 1e-5:
            x0, y0 = 0, int(-c/b)
            x1, y1 = w, int(-(c + a*w)/b)
            cv2.line(img2_lines, (x0, y0), (x1, y1), line_color, 1)
        
        # Draw epipolar line on left image (for right point)
        line = compute_epipolar_line(pt2, F, 2)
        a, b, c = line
        if abs(b) > 1e-5:
            x0, y0 = 0, int(-c/b)
            x1, y1 = w, int(-(c + a*w)/b)
            cv2.line(img1_lines, (x0, y0), (x1, y1), line_color, 1)
    
    return img1_lines, img2_lines

# %%
def compute_and_display_results():
    """
    Computes the Fundamental Matrix and displays results.
    Called either manually (press 'c') or automatically (after 10 points).
    """
    global ref_points_1, ref_points_2, F_matrix, test_mode, img_combined, img1, img2, img_display
    
    # Separate Control Points (first 8) and Test Points (rest)
    ctrl_p1 = ref_points_1[:8]
    ctrl_p2 = ref_points_2[:8]
    
    test_p1 = ref_points_1[8:]
    test_p2 = ref_points_2[8:]
    
    print(f"\nComputing F using {len(ctrl_p1)} control points...")
    F_matrix = compute_fundamental_matrix(ctrl_p1, ctrl_p2)
    
    print("\nFundamental Matrix F:")
    print(F_matrix)
    
    e1, e2 = compute_epipoles(F_matrix)
    print(f"\nEpipole Left: {e1}")
    print(f"Epipole Right: {e2}")
    
    # Check Accuracy
    total_err = 0
    if len(test_p1) > 0:
        print("\nAccuracy Check (Distance to Epipolar Line):")
        for i in range(len(test_p1)):
            # Line in right image for point in left
            l2 = compute_epipolar_line(test_p1[i], F_matrix, 1)
            dist = calculate_distance_to_line(test_p2[i], l2)
            total_err += dist
            print(f"Test Point {i+1}: Distance = {dist:.4f} pixels")
        print(f"Average Error: {total_err/len(test_p1):.4f} pixels")
    else:
        print("\nNo extra points clicked for testing. (Click more than 8 next time!)")
    
    # Draw and display epipolar lines overlay
    print("\n--- Generating Epipolar Lines Overlay ---")
    img1_ctrl, img2_ctrl = draw_epipolar_lines_overlay(img1, img2, ctrl_p1, ctrl_p2, F_matrix, (0, 255, 0))
    
    if len(test_p1) > 0:
        img1_test, img2_test = draw_epipolar_lines_overlay(img1, img2, test_p1, test_p2, F_matrix, (255, 0, 255))
        # Combine control and test lines
        img1_all = cv2.addWeighted(img1_ctrl, 0.5, img1_test, 0.5, 0)
        img2_all = cv2.addWeighted(img2_ctrl, 0.5, img2_test, 0.5, 0)
    else:
        img1_all = img1_ctrl
        img2_all = img2_ctrl
    
    # Show epipolar lines in separate window
    epi_combined = np.hstack((img1_all, img2_all))
    cv2.namedWindow("Epipolar Lines (Green=Control, Magenta=Test)")
    cv2.imshow("Epipolar Lines (Green=Control, Magenta=Test)", epi_combined)
    print("✓ Epipolar lines displayed. Press any key on that window to continue...")
    cv2.waitKey(0)
    cv2.destroyWindow("Epipolar Lines (Green=Control, Magenta=Test)")
    
    # Clean the pictures - create fresh combined image
    img_combined = np.hstack((img1, img2))
    img_display = img_combined.copy()
    cv2.imshow("Stereo Lab", img_display)
    
    print("\n=======================================================")
    print("PART 2: Feature Matching & Analysis")
    print("Click anywhere on the LEFT image to find its match in the RIGHT.")
    print("The search is constrained along the epipolar line.")
    print("")
    print("Commands:")
    print("  - Click LEFT image: Find automatic match + region analysis")
    print("  - Press 'm' then click: Compare automatic vs manual matching")
    print("  - Press 'e': Show epipolar lines overlay again")
    print("  - Press 'r': Generate summary report")
    print("  - Press 's': Save current result image")
    print("  - Press 'q': Quit")
    print("=======================================================")
    test_mode = True

# %% [markdown]
# # ==========================================
# # MAIN
# # ==========================================

# %%



# Load Images
print("Loading pic410.png and pic430.jpg...")
img1 = cv2.imread('./pic410.png')
img2 = cv2.imread('./pic430.png')


# %%
# Resize for easier viewing if too large
img1 = cv2.resize(img1, (0,0), fx=0.5, fy=0.5)
img2 = cv2.resize(img2, (0,0), fx=0.5, fy=0.5)

# Create side-by-side view
img_combined = np.hstack((img1, img2))
img_display = None  # Will be set during test mode

# %%
cv2.namedWindow("Stereo Lab")
cv2.setMouseCallback("Stereo Lab", mouse_callback)

print("=======================================================")
print("PART 1: Manual Calibration")
print("1. Click a point on the LEFT image.")
print("2. Click the corresponding point on the RIGHT image.")
print("3. Repeat at least 8 times (10-12 recommended).")
print("4. Press 'c' to calculate Fundamental Matrix.")
print("=======================================================")


while True:
    # Show the current display (either combined or with markers)
    if img_display is not None:
        cv2.imshow("Stereo Lab", img_display)
    else:
        cv2.imshow("Stereo Lab", img_combined)
    
    key = cv2.waitKey(1) & 0xFF
    
    if key == ord('q'):
        break
        
    elif key == ord('c') and len(ref_points_1) >= 8:
        compute_and_display_results()
    
    elif key == ord('m') and test_mode:
        manual_match_mode = not manual_match_mode
        if manual_match_mode:
            print("\n🔵 MANUAL COMPARISON MODE: Click on LEFT image to find match, then click where YOU think it is on RIGHT")
        else:
            print("Manual comparison mode OFF")
            manual_match_point = None
    
    elif key == ord('e') and test_mode and F_matrix is not None:
        # Re-show epipolar lines
        print("\n--- Re-displaying Epipolar Lines ---")
        ctrl_p1 = ref_points_1[:8]
        ctrl_p2 = ref_points_2[:8]
        test_p1 = ref_points_1[8:]
        test_p2 = ref_points_2[8:]
        
        img1_ctrl, img2_ctrl = draw_epipolar_lines_overlay(img1, img2, ctrl_p1, ctrl_p2, F_matrix, (0, 255, 0))
        if len(test_p1) > 0:
            img1_test, img2_test = draw_epipolar_lines_overlay(img1, img2, test_p1, test_p2, F_matrix, (255, 0, 255))
            img1_all = cv2.addWeighted(img1_ctrl, 0.5, img1_test, 0.5, 0)
            img2_all = cv2.addWeighted(img2_ctrl, 0.5, img2_test, 0.5, 0)
        else:
            img1_all = img1_ctrl
            img2_all = img2_ctrl
        
        epi_combined = np.hstack((img1_all, img2_all))
        cv2.namedWindow("Epipolar Lines (Green=Control, Magenta=Test)")
        cv2.imshow("Epipolar Lines (Green=Control, Magenta=Test)", epi_combined)
        print("Press any key on epipolar window to close...")
        cv2.waitKey(0)
        cv2.destroyWindow("Epipolar Lines (Green=Control, Magenta=Test)")
    
    elif key == ord('s') and img_display is not None:
        # Save current result
        filename = "stereo_result.png"
        cv2.imwrite(filename, img_display)
        print(f"✓ Result saved as {filename}")
    
    elif key == ord('r') and test_mode and F_matrix is not None:
        # Generate report
        print("\n" + "="*60)
        print("STEREO VISION SYSTEM - SUMMARY REPORT")
        print("="*60)
        
        ctrl_p1 = ref_points_1[:8]
        ctrl_p2 = ref_points_2[:8]
        test_p1 = ref_points_1[8:]
        test_p2 = ref_points_2[8:]
        
        print(f"\n1. FUNDAMENTAL MATRIX ESTIMATION")
        print(f"   - Control points used: {len(ctrl_p1)}")
        print(f"   - Test points: {len(test_p1)}")
        print(f"   - Fundamental Matrix F:")
        for row in F_matrix:
            print(f"     [{row[0]:12.8e} {row[1]:12.8e} {row[2]:12.8e}]")
        
        e1, e2 = compute_epipoles(F_matrix)
        print(f"\n2. EPIPOLES")
        print(f"   - Left epipole:  ({e1[0]:.2f}, {e1[1]:.2f})")
        print(f"   - Right epipole: ({e2[0]:.2f}, {e2[1]:.2f})")
        
        if len(test_p1) > 0:
            print(f"\n3. ACCURACY ANALYSIS")
            total_err = 0
            for i in range(len(test_p1)):
                l2 = compute_epipolar_line(test_p1[i], F_matrix, 1)
                dist = calculate_distance_to_line(test_p2[i], l2)
                total_err += dist
            print(f"   - Average epipolar line distance: {total_err/len(test_p1):.4f} pixels")
            print(f"   - Min/Max errors can be seen in individual test point outputs above")
        
        print(f"\n4. FEATURE MATCHING ALGORITHM")
        print(f"   - Method: Sum of Squared Differences (SSD)")
        print(f"   - Search constraint: Along epipolar line")
        print(f"   - Window size: 15x15 pixels")
        print(f"   - Effectiveness: Depends on region type (see analysis below)")
        
        print(f"\n5. KNOWN LIMITATIONS")
        print(f"   - Smooth regions: Low texture makes matching ambiguous")
        print(f"   - Repetitive patterns: Multiple similar windows cause errors")
        print(f"   - Occlusions: Points visible in one image only cannot be matched")
        print(f"   - Illumination: Different lighting affects SSD scores")
        
        print(f"\n" + "="*60)
        print("Use 'm' key to compare automatic vs manual matching performance")
        print("="*60 + "\n")
        
cv2.destroyAllWindows()

# %%



