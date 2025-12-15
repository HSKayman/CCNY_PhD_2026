%===================================================
% Computer Vision Programming Assignment 3
% @Zhigang Zhu, 2003-2009
% City College of New York
% Hasan Kayman
% Calibration
%===================================================
%% Author : Deepak Karuppia  10/15/01

%% Generate 3D calibration pattern: 
%% Pw holds 32 points on two surfaces (Xw = 1 and Yw = 1) of a cube 
%%Values are measured in meters.
%% There are 4x4 uniformly distributed points on each surface.
%% ========================================================================
%  PART 4A: Calibration Pattern "Design"
%  ========================================================================
Pw = []; %world points
cnt = 1;

%% plane : Xw = 1

for i=0.2:0.2:0.8,
 for j=0.2:0.2:0.8,
   Pw(cnt,:) = [1 i j];
   cnt = cnt + 1;
 end
end

%% plane : Yw = 1

for i=0.2:0.2:0.8,
 for j=0.2:0.2:0.8,
   Pw(cnt,:) = [i 1 j];
   cnt = cnt + 1;
 end
end

N = cnt;

plot3(Pw(:,1), Pw(:,2), Pw(:,3), '+');
grid on;
axis equal;
title('3D Calibration Pattern');
xlabel('X_w');
ylabel('Y_w');
zlabel('Z_w');
saveas(gcf, 'q4_3d_pattern.png');
%% Virtual camera model 

%% ========================================================================
%  PART 4B: "Virtual" Camera and Image Generation
%  ======================================================================== 
% Extrinsic parameters : R = RaRbRr

gamma = 40.0*pi/180.0;
Rr = [ [cos(gamma) -sin(gamma) 0];
       [sin(gamma) cos(gamma)  0];
       [  0          0         1]; ];

beta = 0.0*pi/180.0;
Rb = [ [cos(beta) 0 -sin(beta)];
       [0         1       0];
       [sin(beta) 0  cos(beta)]; ];

alpha = -120.0*pi/180.0;
Ra = [ [1      0                0];
       [0   cos(alpha)  -sin(alpha)];
       [0   sin(alpha)   cos(alpha)]; ];

R = Ra*Rb*Rr;

T = [0 0 4]';

%% Intrinsic parameters

f = 16;% in mm
Ox = 256;
Oy = 256;
sensor_width_mm = 8.8;
sensor_height_mm = 6.6;
image_width_px = 512;
image_height_px = 512;

Sx = sensor_width_mm / image_width_px; % pixel size in mm / pixel
Sy = sensor_height_mm / image_height_px; % pixel size in mm / pixel

Fx = f/Sx;
Fy = f/Sy;

%% asr is the aspect ratio
asr = Fx/Fy;

ground_truth.Fx = Fx;
ground_truth.Fy = Fy;
ground_truth.Ox = Ox;
ground_truth.Oy = Oy;
ground_truth.alpha = alpha * 180/pi;
ground_truth.beta  = beta * 180/pi;
ground_truth.gamma = gamma * 180/pi;
ground_truth.R = R;
ground_truth.T = T;

%% Generate Image coordinates
p = []; % image points
Pc = []; % camera coordinates
for i = 1:size(Pw, 1)
    Pc(i, :) = (R * Pw(i, :)' + T)';
    p(i, :) = [(Ox - Fx * Pc(i, 1) / Pc(i, 3)) (Oy - Fy * Pc(i, 2) / Pc(i, 3))];
end

% Plot the 2D "virtual" image
plot(p(1:16, 1), p(1:16, 2), 'r+');
hold on;
plot(p(17:32, 1), p(17:32, 2), 'g+');
axis([0 image_width_px 0 image_height_px]);
set(gca, 'YDir','reverse'); % Set origin to top-left
grid on;
title('Simulated 2D Image of Calibration Pattern');
xlabel('u (pixels)');
ylabel('v (pixels)');
legend('Plane X_w=1', 'Plane Y_w=1');
hold off;
saveas(gcf, 'q4_2d_image.png');

%% ========================================================================
%  PART 4C(i): Direct Calibration Noise-Free One
%  ========================================================================
fprintf('Part 4C(i)');
[params_est_noisefree, M_est_noisefree] = calibrate_camera(Pw, p);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Fx', ground_truth.Fx, params_est_noisefree.Fx);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Fy', ground_truth.Fy, params_est_noisefree.Fy);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Ox', ground_truth.Ox, params_est_noisefree.Ox);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Oy', ground_truth.Oy, params_est_noisefree.Oy);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'alpha (deg)', ground_truth.alpha, params_est_noisefree.alpha);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'beta (deg)', ground_truth.beta, params_est_noisefree.beta);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'gamma (deg)', ground_truth.gamma, params_est_noisefree.gamma);
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Tx (m)', ground_truth.T(1), params_est_noisefree.T(1));
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Ty (m)', ground_truth.T(2), params_est_noisefree.T(2));
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Tz (m)', ground_truth.T(3), params_est_noisefree.T(3));

%% ========================================================================
%  PART 4C(ii): Study on Image Center Estimation
%  ========================================================================
fprintf('Part 4C(ii)');
% Assume a wrong image center
Ox_wrong = 200;
Oy_wrong = 300;
p_shifted = p - [Ox_wrong, Oy_wrong];
[params_est_badcenter, ~] = calibrate_camera(Pw, p_shifted);
fprintf('assumed wrong image center of (%.f, %.f) instead of (%.f, %.f)\n', Ox_wrong, Oy_wrong, Ox, Oy);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Fx', ground_truth.Fx, params_est_badcenter.Fx);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'Fy ', ground_truth.Fy, params_est_badcenter.Fy);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'alpha (deg)', ground_truth.alpha, params_est_badcenter.alpha);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'beta (deg)', ground_truth.beta, params_est_badcenter.beta);
fprintf('%-20s | %-15.2f | %-15.2f\n', 'gamma (deg)', ground_truth.gamma, params_est_badcenter.gamma);
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Tx (m)', ground_truth.T(1), params_est_badcenter.T(1));
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Ty (m)', ground_truth.T(2), params_est_badcenter.T(2));
fprintf('%-20s | %-15.4f | %-15.4f\n', 'Tz (m)', ground_truth.T(3), params_est_badcenter.T(3));
% errors in  image center propagate to all other parameter

%% ========================================================================
%  PART 4C(iii): Accuracy Issues with Noisy Data
%  ========================================================================
fprintf('Part 4C(iii):');
% defining noise levels
noise_3D_m = 0.0001;  % 0.1 mm
noise_2D_px = 0.5;   % 0.5 pixels

% adding noise
Pw_noisy = Pw + (rand(size(Pw)) - 0.5) * 2 * noise_3D_m;
p_noisy = p + (rand(size(p)) - 0.5) * 2 * noise_2D_px;
[params_est_noisy, M_est_noisy] = calibrate_camera(Pw_noisy, p_noisy);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'Fx ', ground_truth.Fx, params_est_noisefree.Fx, params_est_noisy.Fx);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'Fy ', ground_truth.Fy, params_est_noisefree.Fy, params_est_noisy.Fy);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'Ox ', ground_truth.Ox, params_est_noisefree.Ox, params_est_noisy.Ox);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'Oy ', ground_truth.Oy, params_est_noisefree.Oy, params_est_noisy.Oy);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'alpha (deg)', ground_truth.alpha, params_est_noisefree.alpha, params_est_noisy.alpha);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'beta (deg)', ground_truth.beta, params_est_noisefree.beta, params_est_noisy.beta);
fprintf('%-20s | %-15.2f | %-15.2f | %-15.2f\n', 'gamma (deg)', ground_truth.gamma, params_est_noisefree.gamma, params_est_noisy.gamma);
fprintf('%-20s | %-15.4f | %-15.4f | %-15.4f\n', 'Tx (m)', ground_truth.T(1), params_est_noisefree.T(1), params_est_noisy.T(1));
fprintf('%-20s | %-15.4f | %-15.4f | %-15.4f\n', 'Ty (m)', ground_truth.T(2), params_est_noisefree.T(2), params_est_noisy.T(2));
fprintf('%-20s | %-15.4f | %-15.4f | %-15.4f\n', 'Tz (m)', ground_truth.T(3), params_est_noisefree.T(3), params_est_noisy.T(3));

function [params, M_est] = calibrate_camera(Pw, p)
    %number of points
    N=size(Pw, 1);

    % Step 1: forming A matrix for Am = 0 ...
    A = zeros(2 * N, 12);
    for i = 1:N
        X = Pw(i, 1); Y = Pw(i, 2); Z = Pw(i, 3);
        u = p(i, 1); v = p(i, 2);
        A(2*i-1, :) = [X, Y, Z, 1, 0, 0, 0, 0, -u*X, -u*Y, -u*Z, -u];
        A(2*i, :)   = [0, 0, 0, 0, X, Y, Z, 1, -v*X, -v*Y, -v*Z, -v];
    end

    % Step 2: solving for m using SVD ...
    [~, ~, V] = svd(A);
    m = V(:, end); % solution last column V

    % Step 3: reshapinng m into the 3x4 matrix M...
    M_est=reshape(m, 4, 3)';

    % Step 4: decompose M into K, R, T ...
    % M = [m1 m2 m3 | m4] = [M_3x3 | m4]
    M_3x3 = M_est(:, 1:3);
    m4=M_est(:, 4);

    % find rho. the third row of M_3x3 scaled version
    rho = norm(M_3x3(3, :));
    
    % Ensuring Tz is positive. The camera must be in front of the points. if not, flip the sign of the entire projection matrix.
    if M_est(3,4) / rho < 0
        M_est = -M_est;
    end
    
    M_3x3 = M_est(:, 1:3);
    m4 = M_est(:, 4);
    rho = norm(M_3x3(3,:)); % recalculating

    % decompose
    Ox = dot(M_3x3(1,:), M_3x3(3,:)) / rho^2;
    Oy = dot(M_3x3(2,:), M_3x3(3,:)) / rho^2;
    
    % no skew
    Fy = sqrt(dot(M_3x3(2,:), M_3x3(2,:))/rho^2 - Oy^2);
    Fx = sqrt(dot(M_3x3(1,:), M_3x3(1,:))/rho^2 - Ox^2);
    
    % Intrinsic K
    K_est = [Fx, 0,  Ox;
             0,  Fy, Oy;
             0,  0,  1];

    % Decompose M to find extrinsic parameters
    R_est = inv(K_est) * M_3x3 / rho;
    T_est = inv(K_est) * m4 / rho;

    % Step 5: Enforce Orthogonality ...
    [U_r, ~, V_r] = svd(R_est);
    R_final = U_r * V_r';

    % Step 6: Decompose R 
    % R = Rx(alpha) * Ry(beta) * Rz(gamma)
    if R_final(3,1) < 1
        if R_final(3,1) > -1
            beta = asin(-R_final(3,1));
            alpha = atan2(R_final(3,2)/cos(beta), R_final(3,3)/cos(beta));
            gamma = atan2(R_final(2,1)/cos(beta), R_final(1,1)/cos(beta));
        else % R(3,1) = -1, Gimbal lock
            beta = pi/2;
            alpha = -atan2(-R_final(2,3), R_final(2,2));
            gamma = 0;
        end
    else % R(3,1) = 1, Gimbal lock
        beta = -pi/2;
        alpha = atan2(-R_final(2,3), R_final(2,2));
        gamma = 0;
    end

    % Step 7: returning data structure because i am using it more than one place
    params.K = K_est;
    params.Fx = Fx;
    params.Fy = Fy;
    params.Ox = Ox;
    params.Oy = Oy;
    params.R = R_final;
    params.T = T_est;
    params.alpha = alpha * 180 / pi;
    params.beta = beta * 180 / pi;
    params.gamma = gamma * 180 / pi;
end