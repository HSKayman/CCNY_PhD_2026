-- Migration: Add Database-Level Password Policies
-- This addresses Cloud SQL security warnings about password policies
-- Run this after connecting to your Cloud SQL instance

USE ROBOPETY;

-- Try to enable password validation component (MySQL 8.0+)
-- Note: This may fail if plugin is already installed or not available
-- Cloud SQL may have different plugin availability
SET @plugin_exists = 0;
SELECT COUNT(*) INTO @plugin_exists 
FROM INFORMATION_SCHEMA.PLUGINS 
WHERE PLUGIN_NAME = 'validate_password';

-- Only install if not already installed
SET @sql = IF(@plugin_exists = 0, 
    'INSTALL PLUGIN validate_password SONAME ''validate_password.so''',
    'SELECT ''Plugin already installed'' AS status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Set global password validation policy (if plugin is available)
-- These settings enforce strong passwords at the database level
SET @plugin_available = 0;
SELECT COUNT(*) INTO @plugin_available 
FROM INFORMATION_SCHEMA.PLUGINS 
WHERE PLUGIN_NAME = 'validate_password' AND PLUGIN_STATUS = 'ACTIVE';

-- Only set if plugin is available
SET @sql = IF(@plugin_available > 0,
    CONCAT('SET GLOBAL validate_password.length = 8;',
           'SET GLOBAL validate_password.mixed_case_count = 1;',
           'SET GLOBAL validate_password.number_count = 1;',
           'SET GLOBAL validate_password.special_char_count = 1;',
           'SET GLOBAL validate_password.policy = ''MEDIUM'';'),
    'SELECT ''Password validation plugin not available - using application-level policy only'' AS status');
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Apply password policy to existing root user (MySQL 8.0+ syntax)
-- Note: This won't change existing password, but will enforce policy on password changes
-- This works even if validate_password plugin is not available
ALTER USER 'root'@'%' 
    REQUIRE PASSWORD_LENGTH 8
    PASSWORD_REQUIRE_UPPERCASE
    PASSWORD_REQUIRE_LOWERCASE
    PASSWORD_REQUIRE_NUMBER
    PASSWORD_REQUIRE_SPECIAL;

-- If you have other users, apply the same policy
-- Example for application users (adjust as needed):
-- ALTER USER 'app_user'@'%' 
--     REQUIRE PASSWORD_LENGTH 8
--     PASSWORD_REQUIRE_UPPERCASE
--     PASSWORD_REQUIRE_LOWERCASE
--     PASSWORD_REQUIRE_NUMBER
--     PASSWORD_REQUIRE_SPECIAL;

-- Verify password policy is active (if plugin is available)
SELECT 
    CASE 
        WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME = 'validate_password' AND PLUGIN_STATUS = 'ACTIVE')
        THEN CONCAT('Password validation plugin: ACTIVE')
        ELSE 'Password validation plugin: NOT AVAILABLE (using application-level policy)'
    END AS plugin_status,
    CASE 
        WHEN EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.PLUGINS WHERE PLUGIN_NAME = 'validate_password' AND PLUGIN_STATUS = 'ACTIVE')
        THEN CONCAT('Min length: ', @@validate_password.length, 
                   ', Mixed case: ', @@validate_password.mixed_case_count,
                   ', Numbers: ', @@validate_password.number_count,
                   ', Special chars: ', @@validate_password.special_char_count,
                   ', Policy: ', @@validate_password.policy)
        ELSE 'Database-level password requirements set via ALTER USER'
    END AS policy_details;

