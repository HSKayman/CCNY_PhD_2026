%===================================================
% Computer Vision Programming Assignment 2
% @Zhigang Zhu, 2003-2009
% City College of New York
% Hasan Kayman
% Histogram Analysis and Image Enhancement
%===================================================
set(0, 'DefaultFigureWindowState', 'maximized');
% Read in an image, get information
InputImage = 'IDPicture.bmp'; 
img = imread(InputImage);
%% ---------------- Question 1 ------------------------

% Display the three separate bands with the color image 
img_gray = rgb2gray(img); % Convert to grayscale if color

% Convert to double for processing
img_gray = double(img_gray);

% Q1.1. Original Image and Histogram
No1 = figure();

% Display original image
subplot(3,4,1);
imshow(uint8(img_gray));
title('Original Image');

% Original histogram
subplot(3,4,2);
histogram(img_gray(:), 0:255, 'FaceColor', 'blue');
title('Original Histogram');
xlabel('Intensity'); 
ylabel('Frequency');

% 1.2. Contrast Enhancement
% Find min and max values
min_val = min(img_gray(:));
max_val = max(img_gray(:));

% Linear contrast basically scaling
img_contrast = (img_gray - min_val) * 255 / (max_val - min_val);

subplot(3,4,3);
imshow(uint8(img_contrast));
title('Contrast Enhanced');

subplot(3,4,4);
histogram(img_contrast(:), 0:255, 'FaceColor', 'red');
title('Contrast Enhanced Histogram');
xlabel('Intensity'); 
ylabel('Frequency');

% 1.3. Histogram Equalization
img_eq = histeq(uint8(img_gray));

subplot(3,4,5);
imshow(img_eq);
title('Histogram Equalized');

subplot(3,4,6);
histogram(img_eq(:), 0:255, 'FaceColor', 'green');
title('Equalized Histogram');
xlabel('Intensity'); ylabel('Frequency');

%%4. Thresholding
threshold = graythresh(uint8(img_gray)) * 255; 
% I find it with AI Mode Search If not accepted I would select 125 because this is maxima point in histogram
img_thresh = img_gray > threshold;
img_thresh= img_thresh*255;
subplot(3,4,7);
imshow(img_thresh);
title(['Thresholded (' num2str(round(threshold)) ')']);

subplot(3,4,8);
histogram(double(img_thresh(:)), 0:255, 'FaceColor', 'magenta');
title('Thresholded Histogram');
xlabel('Intensity'); ylabel('Frequency');
saveas(No1, 'a2_1.png');
%% ---------------- Question 2 ------------------------
% Edge Detection: Sobel Operator Comparison

% Image 1: Ideal man-made image
img1 = imread('coins.png');
img1_double = im2double(img1);

% Image 2: Real scene with more details
img2 = imread('cameraman.tif');
img2_double = im2double(img2);

% 2.2: Define Gradient Operators

% 1x2 Operator
% Horizontal gradient: [-1 1] (detects vertical edges)
% Vertical gradient: [-1; 1] (detects horizontal edges)
operator_1x2_h = [-1, 1];      % (vertical edges)
operator_1x2_v = [-1; 1];      % (horizontal edges)

fprintf('1x2 Horizontal operator:\n');
disp(operator_1x2_h);
fprintf('1x2 Vertical operator:\n');
disp(operator_1x2_v);

% Sobel operators
Sx = [-1 0 1; -2 0 2; -1 0 1];
Sy = Sx';

images = {img1_double, img2_double};
image_names = {'Man-made Image', 'Real Scene Image'};

for img_idx = 1:2
    current_img = images{img_idx};
    
    % Apply 1x2 operators using convolution
    grad_1x2_h = conv2(current_img, operator_1x2_h, 'same');
    grad_1x2_v = conv2(current_img, operator_1x2_v, 'same');
    
    % Apply Sobel operators
    grad_sobel_h = conv2(current_img, Sx, 'same');
    grad_sobel_v = conv2(current_img, Sy, 'same');
    
    % Magnitudes
    mag_1x2 = sqrt(grad_1x2_h.^2 + grad_1x2_v.^2);
    mag_sobel = sqrt(grad_sobel_h.^2 + grad_sobel_v.^2);
    
    % Normalize signed gradients to [-1,1] for analysis; display abs(.)
    grad_1x2_h_signed = normalize_signed(grad_1x2_h);
    grad_1x2_v_signed = normalize_signed(grad_1x2_v);
    grad_sobel_h_signed = normalize_signed(grad_sobel_h);
    grad_sobel_v_signed = normalize_signed(grad_sobel_v);
    
    % For display purposes, map to [0, 255]
    grad_1x2_h_norm = normalize_gradient(abs(grad_1x2_h_signed));
    grad_1x2_v_norm = normalize_gradient(abs(grad_1x2_v_signed));
    grad_sobel_h_norm = normalize_gradient(abs(grad_sobel_h_signed));
    grad_sobel_v_norm = normalize_gradient(abs(grad_sobel_v_signed));
    mag_1x2_norm = normalize_gradient(mag_1x2);
    mag_sobel_norm = normalize_gradient(mag_sobel);
    
    % Residual between normalized magnitudes (Sobel - 1x2), re-normalized for display
    residual = im2double(mag_sobel_norm) - im2double(mag_1x2_norm);
    residual_disp = normalize_gradient(residual);  % for visualization
    
    % Store results for comparison
    S = struct('original', current_img, ...
        'grad_1x2_h', grad_1x2_h, 'grad_1x2_v', grad_1x2_v, ...
        'mag_1x2', mag_1x2, 'grad_1x2_h_norm', grad_1x2_h_norm, ...
        'grad_1x2_v_norm', grad_1x2_v_norm, 'mag_1x2_norm', mag_1x2_norm, ...
        'grad_sobel_h_norm', grad_sobel_h_norm, 'grad_sobel_v_norm', grad_sobel_v_norm, ...
        'mag_sobel_norm', mag_sobel_norm, 'residual_disp', residual_disp);
    if img_idx == 1
        results_img1 = S;
    else
        results_img2 = S;
    end
end

No2 = figure();

% Rows 1-2: Man-made Image Analysis
subplot(4,6,1);
imshow(uint8(results_img1.original*255));
title('Man-made Original');

subplot(4,6,2);
imshow(uint8(results_img1.grad_1x2_h_norm));
title('1x2 |Gx|');

subplot(4,6,3);
imshow(uint8(results_img1.grad_1x2_v_norm));
title('1x2 |Gy|');

subplot(4,6,4);
imshow(uint8(results_img1.mag_1x2_norm));
title('1x2 Magnitude');

subplot(4,6,5);
imshow(uint8(results_img1.grad_sobel_h_norm));
title('Sobel |Gx|');

subplot(4,6,6);
imshow(uint8(results_img1.grad_sobel_v_norm));
title('Sobel |Gy|');

% Second row for man-made image
subplot(4,6,7);
imshow(uint8(results_img1.mag_sobel_norm));
title('Sobel Magnitude');

subplot(4,6,8);
imshow(uint8(results_img1.residual_disp));
title('Residual (Sobel-1x2)');

subplot(4,6,9);
histogram(results_img1.mag_1x2_norm(:), 0:10:255, 'FaceColor', 'blue');
title('Mag Dist 1x2 (Man-made)');
xlabel('Magnitude Value');

subplot(4,6,10);
histogram(results_img1.mag_sobel_norm(:), 0:10:255, 'FaceColor', 'red');
title('Mag Dist Sobel (Man-made)');
xlabel('Magnitude Value');

subplot(4,6,11);
threshold1 = 0.5 * max(results_img1.mag_sobel_norm(:)); % use Sobel-based threshold
imshow(uint8(results_img1.mag_1x2_norm > threshold1) * 255);
title('1x2 Binary Edges');

subplot(4,6,12);
imshow(uint8(results_img1.mag_sobel_norm > threshold1) * 255);
title('Sobel Binary Edges');

% Rows 3-4: Real Scene Image Analysis
subplot(4,6,13);
imshow(results_img1.original)
title('Real Scene Original');

subplot(4,6,14);
imshow(uint8(results_img2.grad_1x2_h_norm));
title('1x2 |Gx|');

subplot(4,6,15);
imshow(uint8(results_img2.grad_1x2_v_norm));
title('1x2 |Gy|');

subplot(4,6,16);
imshow(uint8(results_img2.mag_1x2_norm));
title('1x2 Magnitude');

subplot(4,6,17);
imshow(uint8(results_img2.grad_sobel_h_norm));
title('Sobel |Gx|');

subplot(4,6,18);
imshow(uint8(results_img2.grad_sobel_v_norm));
title('Sobel |Gy|');

% Fourth row for real scene image
subplot(4,6,19);
imshow(uint8(results_img2.mag_sobel_norm));
title('Sobel Magnitude');

subplot(4,6,20);
imshow(uint8(results_img2.residual_disp));
title('Residual (Sobel-1x2)');

subplot(4,6,21);
histogram(results_img2.mag_1x2_norm(:), 0:10:255, 'FaceColor', 'blue');
title('Mag Dist 1x2 (Real)');
xlabel('Magnitude Value');

subplot(4,6,22);
histogram(results_img2.mag_sobel_norm(:), 0:10:255, 'FaceColor', 'red');
title('Mag Dist Sobel (Real)');
xlabel('Magnitude Value');

subplot(4,6,23);
threshold2 = 0.5 * max(results_img2.mag_sobel_norm(:));
imshow(uint8(results_img2.mag_1x2_norm > threshold2) * 255);
title('1x2 Binary Edges');

subplot(4,6,24);
imshow(uint8(results_img2.mag_sobel_norm > threshold2) * 255);
title('Sobel Binary Edges');

function out = normalize_signed(G)
    % Normalize signed gradient to [-1,1]
    maxabs = max(abs(G(:)));
    if maxabs < eps
        out = zeros(size(G));
    else
        out = G ./ maxabs;
    end
end

function normalized_img = normalize_gradient(img)
    % Normalize image to [0, 255] range for display
    img = double(img);
    min_val = min(img(:));
    max_val = max(img(:));
    if max_val == min_val
        normalized_img = zeros(size(img));
    else
        normalized_img = (img - min_val) * 255 / (max_val - min_val);
    end
end


saveas(No2, 'a2_2.png');


%% ---------------- Question 3 ------------------------
% Edge Map Generation
% Test different percentages
percentages = [1, 5, 10, 15, 20];
images_data = {results_img1, results_img2};
image_names = {'Man-made', 'Real Scene'};

% Create single comprehensive figure
No3 = figure();

% Row 1-2: Percentage comparison for both images
for img_idx = 1:2
    current_data = images_data{img_idx};
    magnitude = current_data.mag_1x2_norm;
    
    % Show original
    subplot(4, 6, (img_idx-1)*6 + 1);
    imshow(current_data.original);
    title([image_names{img_idx} ' Original']);
    
    % Test different percentages
    for p_idx = 1:length(percentages)
        percentage = percentages(p_idx);
        
        % Calculate threshold
        sorted_magnitudes = sort(magnitude(:), 'descend');
        num_edge_pixels = round(length(sorted_magnitudes) * percentage / 100);
        threshold = sorted_magnitudes(num_edge_pixels);
        
        % Generate edge map
        edge_map = magnitude >= threshold;
        
        % Display
        subplot(4, 6, (img_idx-1)*6 + 1 + p_idx);
        imshow(edge_map);
        title([num2str(percentage) '%']);
        
    end
end

% Row 3: Adaptive thresholding

for img_idx = 1:2
    current_data = images_data{img_idx};
    magnitude = current_data.mag_1x2_norm;
    
    % Simple adaptive: mean + std as threshold
    local_threshold = mean(magnitude(:)) + std(magnitude(:));
    adaptive_edge_map = magnitude >= local_threshold;
    
    subplot(4, 6, 12 + img_idx*2 - 1);
    imshow(uint8(magnitude));
    title([image_names{img_idx} ' Magnitude']);
    
    subplot(4, 6, 12 + img_idx*2);
    imshow(adaptive_edge_map);
    title([image_names{img_idx} ' Adaptive']);
    
end

% Use 5% threshold for sketch
id_magnitude = sqrt(results_img1.grad_1x2_h.^2 + results_img1.grad_1x2_v.^2);
id_magnitude_norm = normalize_gradient(id_magnitude);

sorted_id = sort(id_magnitude_norm(:), 'descend');
sketch_pixels = round(length(sorted_id) * 0.05); % 5%
sketch_threshold = sorted_id(sketch_pixels);
id_sketch = id_magnitude_norm >= sketch_threshold;

subplot(4, 6, 19);
imshow(results_img1.original);
title('Original ID');

subplot(4, 6, 20);
imshow(uint8(id_magnitude_norm));
title('ID Magnitude');

subplot(4, 6, 21);
imshow(id_sketch);
title('ID Sketch (5%)');
saveas(No3, 'a2_3.png');
%% ---------------- Question 4 ------------------------
% Kernel Size Comparison: 1x2, 3x3, 5x5, 7x7
% Define kernels
% 1x2 kernels (already used)
kernel_1x2_h = [-1, 1];
kernel_1x2_v = [-1; 1];

% 3x3 Sobel kernels
kernel_3x3_h = [-1 0 1; -2 0 2; -1 0 1];
kernel_3x3_v = [-1 -2 -1; 0 0 0; 1 2 1];

% 5x5 kernels
kernel_5x5_h = [-1 -2 0 2 1; -2 -3 0 3 2; -3 -5 0 5 3; -2 -3 0 3 2; -1 -2 0 2 1];
kernel_5x5_v = kernel_5x5_h';

% 7x7 kernels
kernel_7x7_h = [-1 -2 -3 0 3 2 1; -2 -3 -4 0 4 3 2; -3 -4 -5 0 5 4 3; 
                -4 -5 -6 0 6 5 4; -3 -4 -5 0 5 4 3; -2 -3 -4 0 4 3 2; 
                -1 -2 -3 0 3 2 1];
kernel_7x7_v = kernel_7x7_h';

kernels_h = {kernel_1x2_h, kernel_3x3_h, kernel_5x5_h, kernel_7x7_h};
kernels_v = {kernel_1x2_v, kernel_3x3_v, kernel_5x5_v, kernel_7x7_v};
kernel_names = {'1x2', '3x3', '5x5', '7x7'};
% Test on both images
test_images = {img1, img2};
image_names = {'ID Image', 'Real Scene'};

% Create single figure
No4 = figure();


for img_idx = 1:2
    current_img = test_images{img_idx};
    
    for k_idx = 1:4
        kernel_h = kernels_h{k_idx};
        kernel_v = kernels_v{k_idx};
        
        grad_h = conv2(double(current_img), kernel_h, 'same');
        grad_v = conv2(double(current_img), kernel_v, 'same');
        magnitude = sqrt(grad_h.^2 + grad_v.^2);
        
        % Calculate operations
        [rows, cols] = size(current_img);
        kernel_size = size(kernel_h, 1) * size(kernel_h, 2);
        total_ops = rows * cols * kernel_size * 2;

        % Display results
        subplot_idx = (img_idx-1)*8 + k_idx*2 - 1;
        
        subplot(4, 8, subplot_idx);
        imshow(uint8(abs(grad_h)));
        title([kernel_names{k_idx} ' Horizontal']);
        
        subplot(4, 8, subplot_idx + 1);
        imshow(uint8(magnitude));
        title([kernel_names{k_idx} ' Magnitude']);
    end
    
    % Show original
    subplot(4, 8, (img_idx-1)*8 + 1);
    imshow(uint8(current_img));
    title([image_names{img_idx} ' Original']);
end
% Add noise to first image
noisy_img = imnoise(uint8(img1), 'gaussian', 0, 0.01);

for k_idx = 1:4
    kernel_h = kernels_h{k_idx};
    kernel_v = kernels_v{k_idx};
    
    % Apply to noisy image
    grad_h_noisy = conv2(double(noisy_img), kernel_h, 'same');
    grad_v_noisy = conv2(double(noisy_img), kernel_v, 'same');
    magnitude_noisy = sqrt(grad_h_noisy.^2 + grad_v_noisy.^2);
    
    % Display
    subplot(4, 8, 16 + k_idx*2);
    imshow(uint8(magnitude_noisy));
    title([kernel_names{k_idx} ' Noisy']);
    
    % Calculate noise sensitivity
    noise_level = std(magnitude_noisy(:));
end

subplot(4, 8, 17);
imshow(uint8(noisy_img));
title('Noisy Original');
saveas(No4, 'a2_4.png');
%% ---------------- Question 5 ------------------------
% Color Edge Detection

InputImage = 'IDPicture.bmp'; 
img = imread(InputImage);

[rows, cols, ~] = size(color_img);

% Extract RGB channels
R = double(color_img(:,:,1));
G = double(color_img(:,:,2));
B = double(color_img(:,:,3));

% Convert to grayscale for comparison
gray_img = 0.299*R + 0.587*G + 0.114*B; %STANDARD

% Define 1x2 and 2x1 kernels
sobel_h = [-1, 1];      % 1x2 horizontal
sobel_v = [-1; 1];      % 2x1 vertical

%%Method 1: Apply Sobel to each RGB channel separately
fprintf('\nApplying Sobel to RGB channels...\n');

% R channel gradients
R_grad_h = conv2(R, sobel_h, 'same');
R_grad_v = conv2(R, sobel_v, 'same');
R_magnitude = sqrt(R_grad_h.^2 + R_grad_v.^2);

% G channel gradients
G_grad_h = conv2(G, sobel_h, 'same');
G_grad_v = conv2(G, sobel_v, 'same');
G_magnitude = sqrt(G_grad_h.^2 + G_grad_v.^2);

% B channel gradients
B_grad_h = conv2(B, sobel_h, 'same');
B_grad_v = conv2(B, sobel_v, 'same');
B_magnitude = sqrt(B_grad_h.^2 + B_grad_v.^2);

% Method 2: Combine RGB gradients
% Method 2a: Sum of magnitudes
combined_magnitude = R_magnitude + G_magnitude + B_magnitude;

% Method 2b: Maximum of magnitudes
max_magnitude = max(cat(3, R_magnitude, G_magnitude, B_magnitude), [], 3);

% Method 2c: Euclidean combination
euclidean_magnitude = sqrt(R_magnitude.^2 + G_magnitude.^2 + B_magnitude.^2);

% Method 3: Grayscale edge detection
gray_grad_h = conv2(gray_img, sobel_h, 'same');
gray_grad_v = conv2(gray_img, sobel_v, 'same');
gray_magnitude = sqrt(gray_grad_h.^2 + gray_grad_v.^2);

% Generate edge maps with 5% threshold
methods = {R_magnitude, G_magnitude, B_magnitude, combined_magnitude, ...
           max_magnitude, euclidean_magnitude, gray_magnitude};
method_names = {'R Channel', 'G Channel', 'B Channel', 'Sum RGB', ...
                'Max RGB', 'Euclidean RGB', 'Grayscale'};

edge_maps = cell(1, length(methods));
thresholds = zeros(1, length(methods));

for i = 1:length(methods)
    magnitude = methods{i};
    sorted_mag = sort(magnitude(:), 'descend');
    threshold_idx = round(length(sorted_mag) * 0.05); % 5%
    threshold = sorted_mag(threshold_idx);
    
    edge_maps{i} = magnitude >= threshold;
    thresholds(i) = threshold;
    fprintf('%s: threshold=%.1f, edges=%d\n', method_names{i}, threshold, sum(edge_maps{i}(:)));
end

% Create color edge map

% Use maximum gradient method for color edges
color_edge_map = zeros(rows, cols, 3);

% Find which channel has maximum gradient at each pixel
[~, max_channel] = max(cat(3, R_magnitude, G_magnitude, B_magnitude), [], 3);

% Assign colors based on dominant gradient channel
for i = 1:rows
    for j = 1:cols
        if max_magnitude(i,j) >= thresholds(5) % Use max RGB threshold
            switch max_channel(i,j)
                case 1 % R dominant
                    color_edge_map(i,j,:) = [1, 0, 0]; % Red
                case 2 % G dominant
                    color_edge_map(i,j,:) = [0, 1, 0]; % Green
                case 3 % B dominant
                    color_edge_map(i,j,:) = [0, 0, 1]; % Blue
            end
        end
    end
end

% Display results in one figure
No5=figure();

% Row 1: Original and RGB channels
subplot(3, 7, 1);
imshow(uint8(color_img));
title('Original Color');

subplot(3, 7, 2);
imshow(uint8(R));
title('R Channel');

subplot(3, 7, 3);
imshow(uint8(G));
title('G Channel');

subplot(3, 7, 4);
imshow(uint8(B));
title('B Channel');

subplot(3, 7, 5);
imshow(uint8(gray_img));
title('Grayscale');

% Row 2: Individual channel edge maps
for i = 1:3
    subplot(3, 7, 7 + i);
    imshow(edge_maps{i});
    title([method_names{i} ' Edges']);
end

% Row 3: Combined methods
for i = 4:7
    subplot(3, 7, 7 + i);
    imshow(edge_maps{i});
    title([method_names{i} ' Edges']);
end

% Row 4: Color edge map and sketch
subplot(3, 7, 16);
imshow(color_edge_map);
title('Color Edge Map');

% Generate color sketch

% Create color sketch by overlaying color edges on original
color_sketch = double(color_img) / 255;
edge_overlay = max_magnitude >= thresholds(5);

% Enhance edges in sketch
for c = 1:3
    channel = color_sketch(:,:,c);
    channel(edge_overlay) = channel(edge_overlay) * 1.5; % Brighten edges
    color_sketch(:,:,c) = min(channel, 1); % Clamp to [0,1]
end

subplot(3, 7, 17);
imshow(color_sketch);
title('Color Sketch');

% Adaptive color thresholding

% Simple adaptive: mean + std for each channel
adaptive_edge_map = false(rows, cols);
for c = 1:3
    channel_mag = methods{c};
    adaptive_threshold = mean(channel_mag(:)) + std(channel_mag(:));
    adaptive_edge_map = adaptive_edge_map | (channel_mag >= adaptive_threshold);
end

subplot(3, 7, 18);
imshow(adaptive_edge_map);
title('Adaptive Color Edges');
saveas(No5, 'a2_5.png');