%===================================================
% Computer Vision Programming Assignment 1
% @Zhigang Zhu, 2003-2009
% City College of New York
%===================================================
set(0, 'DefaultFigureWindowState', 'maximized');
% ---------------- Step 1 ------------------------
% Read in an image, get information
InputImage = 'IDPicture.bmp'; 
C1 = imread(InputImage);
[ROWS COLS CHANNELS] = size(C1);
image(C1);
title('Question 1: Real Image');
imwrite(uint8(C1), 'q1.png');
% ---------------- Step 2 ------------------------
% Display the three separate bands with the color image

CR1 = uint8(zeros(ROWS, COLS, CHANNELS));
for band = 1 : CHANNELS,
    CR1(:,:,band) = (C1(:,:,1));
end

CG1 =uint8(zeros(ROWS, COLS, CHANNELS));
for band = 1 : CHANNELS,
    CG1(:,:,band) = (C1(:,:,2));
end

CB1 =uint8(zeros(ROWS, COLS, CHANNELS));
for band = 1 : CHANNELS,
    CB1(:,:,band) = (C1(:,:,3));
end

No1 = figure;
disimg = [C1, CR1; CG1, CB1]; 
image(disimg);
title('Question 2: Top [Real,Red] Bottom [Green, Blue]');
saveas(No1, 'q2.png');
% ---------------- Step 3 ------------------------
% Generate intensity image using NTSC standard
% NTSC standard: I = 0.299R + 0.587G + 0.114B
I_NTSC = uint8(round(0.299*double(C1(:,:,1)) + ...
                    0.587*double(C1(:,:,2)) + ...
                    0.114*double(C1(:,:,3))));

% Simple average intensity
I_avg = uint8(round(sum(C1,3)/3));

% Calculate and display the difference
diff_image = uint8(abs(double(I_NTSC) - double(I_avg)));

% Create grayscale colormap
MAP = zeros(256, 3);
for i = 1 : 256,
    for band = 1:CHANNELS,
        MAP(i,band) = (i-1)/255;
    end 
end

% Display NTSC intensity image
No2 = figure;
subplot(2,2,1);
image(I_NTSC);
colormap(MAP);
title('Question 3: NTSC Intensity Image');

% Display average intensity image
subplot(2,2,2);
image(I_avg);
colormap(MAP);
title('Question 3: Average Intensity Image');

% Display difference image
subplot(2,2,3);
image(diff_image);
colormap(MAP);
title('Question 3: Difference Image (NTSC - Average)');

% Display histogram of differences
subplot(2,2,4);
hist(double(diff_image(:)), 50);
title('Question 3: Histogram of Differences');
xlabel('Difference Value');
ylabel('Frequency');

% Calculate statistics
mean_diff = mean(diff_image(:));
max_diff = max(diff_image(:));
fprintf('Mean difference: %.2f\n', mean_diff);
fprintf('Maximum difference: %d\n', max_diff);
saveas(No2, 'q3.png');
% ---------------- Step 4 ------------------------
K_values = [4, 16, 32, 64];
No3 = figure;

for idx = 1:length(K_values)
    K = K_values(idx);
    
    % Calculate quantization levels
    levels = linspace(0, 255, K); % if k=2 it returns [0, 255]
    quantized = zeros(size(I_NTSC));
    I_double = double(I_NTSC);

    % Quantize the image
    for i = 1:numel(I_double)
        % Calculate distances to all quantization levels
        distances = abs(I_double(i) - levels);
        
        % Find the closest level
        [~, closest_idx] = min(distances);
        
        % Assign to the closest level
        quantized(i) = levels(closest_idx);
    end
    
    quantized = uint8(quantized);
    
    % Display quantized image
    subplot(2,2,idx);
    image(quantized);
    colormap(MAP);
    title(sprintf('Question 4: Quantized to %d levels', K));
end
saveas(No3, 'q4.png');
% ---------------- Step 5 ------------------------
% Quantize color image to K levels (K=2 and K=4 for each band)
K_color_values = [2, 4, 8, 16];
No4 = figure;

for idx = 1:length(K_color_values)
    K = K_color_values(idx);
    
    % Initialize quantized color image
    C_quantized = zeros(size(C1));
    
    % Quantize each color channel
    for channel = 1:3
        levels = linspace(0, 255, K);
        channel_data = double(C1(:,:,channel));
        quantized_channel = zeros(size(channel_data));
        
       % Quantize the image
        for i = 1:numel(channel_data)
            % Calculate distances to all quantization levels
            distances = abs(channel_data(i) - levels);
            
            % Find the closest level
            [~, closest_idx] = min(distances);
            
            % Assign to the closest level
            quantized_channel(i) = levels(closest_idx);
        end
       
        C_quantized(:,:,channel) = quantized_channel;
    end
    
    C_quantized = uint8(C_quantized);
    
    % Display quantized color image
    subplot(2,2,idx);
    image(C_quantized);
    title(sprintf('Question 5: Color Quantized to %d levels per band', K));
end
saveas(No4, 'q5.png');
% ---------------- Step 6 ------------------------
% Logarithmic quantization of color image
% We need to find C such that when I = 255, I' = 255
% I' = C * ln(I + 1)
% 255 = C * ln(255 + 1)
% 255 = C * ln(256)
% C = 255 / ln(256)

C = 255 / log(256); 
fprintf('Optimal C value: %.3f\n', C);

% Verify: when I = 0, I' = C * ln(1) = C * 0 = 0 ✓
% Verify: when I = 255, I' = C * ln(256) = 255 ✓

% Apply logarithmic quantization to each color channel
CL = zeros(size(C1));

for channel = 1:3
    % Get the channel data
    I = double(C1(:,:,channel));
    
    % Apply logarithmic transformation
    I_prime = C * log(I + 1);
    
    % Ensure values are in range [0, 255] and convert to uint8
    CL(:,:,channel) = uint8(round(I_prime));
end

% Display original and logarithmically quantized images
No5 = figure;
subplot(1,2,1);
imshow(C1);
title('Question 6: Original Color Image');

subplot(1,2,2);
imshow(uint8(CL));
title('Question 6: Logarithmically Quantized Color Image');
saveas(No5, 'q6.png');

