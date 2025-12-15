"""Secrets manager with Google Secret Manager support and env fallback."""
import os
import logging

logger = logging.getLogger(__name__)

# Try to import Google Secret Manager
try:
    from google.cloud import secretmanager
    SECRET_MANAGER_AVAILABLE = True
except ImportError:
    SECRET_MANAGER_AVAILABLE = False
    logger.warning("Google Secret Manager not available, using environment variables only")


def _get_project_id() -> str:
    """
    Get GCP project ID from various sources.
    
    Returns:
        Project ID string or empty string if not found
    """
    # Try standard environment variables (App Engine sets GOOGLE_CLOUD_PROJECT)
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")
    if project_id:
        logger.debug(f"Found project ID from environment: {project_id}")
        return project_id
    
    # Try to extract from CLOUD_SQL_CONNECTION_NAME (format: PROJECT_ID:REGION:INSTANCE)
    connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME", "")
    if connection_name and ":" in connection_name:
        parts = connection_name.split(":")
        if len(parts) >= 3:
            project_id = parts[0]
            logger.debug(f"Extracted project ID from connection name: {project_id}")
            return project_id
    
    # Try to get from App Engine metadata service (if running on App Engine)
    try:
        import requests
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/project/project-id"
        response = requests.get(metadata_url, headers={"Metadata-Flavor": "Google"}, timeout=2)
        if response.status_code == 200:
            project_id = response.text.strip()
            logger.debug(f"Found project ID from metadata service: {project_id}")
            return project_id
    except Exception:
        pass  # Not running on App Engine or metadata service unavailable
    
    logger.warning("Could not determine project ID from any source")
    return ""


def get_secret(secret_name: str, project_id: str = None, default: str = None, prefer_secret_manager: bool = False) -> str:
    """
    Fetch secret from Google Secret Manager or environment variable.
    
    Args:
        secret_name: Name of the secret (in Secret Manager) or env var
        project_id: GCP project ID (optional, will try to detect)
        default: Default value if secret not found
        prefer_secret_manager: If True, try Secret Manager first before env vars
        
    Returns:
        Secret value as string
    """
    # If prefer_secret_manager is True, try Secret Manager first
    if prefer_secret_manager and SECRET_MANAGER_AVAILABLE:
        try:
            if not project_id:
                project_id = _get_project_id()
            
            if project_id:
                client = secretmanager.SecretManagerServiceClient()
                secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
                
                logger.debug(f"Attempting to fetch {secret_name} from Secret Manager first (project: {project_id})")
                response = client.access_secret_version(request={"name": secret_path})
                secret_value = response.payload.data.decode("UTF-8").strip()
                
                if secret_value:
                    logger.info(f"Successfully fetched {secret_name} from Secret Manager (preferred)")
                    return secret_value
                else:
                    logger.warning(f"Secret {secret_name} found in Secret Manager but value is empty")
        except Exception as e:
            logger.warning(f"Failed to fetch {secret_name} from Secret Manager (preferred): {e}")
            logger.debug(f"Secret Manager error details: {type(e).__name__}: {str(e)}")
    
    # Try environment variable (for local dev and app.yaml)
    env_value = os.environ.get(secret_name)
    if env_value and env_value.strip():
        logger.info(f"Using environment variable for {secret_name} (length: {len(env_value)})")
        return env_value
    
    # Try Google Secret Manager if available
    if SECRET_MANAGER_AVAILABLE:
        try:
            if not project_id:
                project_id = _get_project_id()
                if not project_id:
                    logger.warning(f"No project_id available for {secret_name}, cannot use Secret Manager")
                    if default is not None:
                        return default
                    return ""
            
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            
            logger.debug(f"Attempting to fetch {secret_name} from Secret Manager (project: {project_id})")
            response = client.access_secret_version(request={"name": secret_path})
            secret_value = response.payload.data.decode("UTF-8").strip()
            
            if secret_value:
                logger.info(f"Successfully fetched {secret_name} from Secret Manager")
                return secret_value
            else:
                logger.warning(f"Secret {secret_name} found in Secret Manager but value is empty")
        except Exception as e:
            logger.warning(f"Failed to fetch {secret_name} from Secret Manager: {e}")
            logger.debug(f"Secret Manager error details: {type(e).__name__}: {str(e)}")
    
    # Return default or empty string
    if default is not None:
        logger.debug(f"Using default value for {secret_name}")
        return default
    
    logger.warning(f"Secret {secret_name} not found in env or Secret Manager, returning empty string")
    return ""


def get_jwt_secret(project_id: str = None) -> str:
    """Get JWT secret from Secret Manager or env."""
    return get_secret("JWT_SECRET", project_id, default="dev-jwt-secret-change-in-production")


def get_flask_secret(project_id: str = None) -> str:
    """Get Flask secret from Secret Manager or env."""
    return get_secret("FLASK_SECRET", project_id, default=get_jwt_secret(project_id))


def get_db_password(project_id: str = None) -> str:
    """Get database password from Secret Manager or env."""
    # Prefer Secret Manager for database password to allow override of app.yaml values
    return get_secret("CLOUD_SQL_PASSWORD", project_id, default="", prefer_secret_manager=True)


def get_db_user(project_id: str = None) -> str:
    """Get database user from Secret Manager or env."""
    return get_secret("CLOUD_SQL_USERNAME", project_id, default="root")


def get_db_name(project_id: str = None) -> str:
    """Get database name from Secret Manager or env."""
    return get_secret("CLOUD_SQL_DATABASE_NAME", project_id, default="ROBOPETY")


def get_db_connection_name(project_id: str = None) -> str:
    """Get database connection name from Secret Manager or env."""
    return get_secret("CLOUD_SQL_CONNECTION_NAME", project_id, default="")


def get_bucket_name(project_id: str = None) -> str:
    """Get bucket name from Secret Manager or env."""
    return get_secret("BUCKET_NAME", project_id, default="")


def get_recaptcha_site_key(project_id: str = None) -> str:
    """Get reCAPTCHA site key (public key) from Secret Manager or env."""
    # Prefer Secret Manager for reCAPTCHA to allow override of app.yaml values
    return get_secret("RECAPTCHA_SITE_KEY", project_id, default="", prefer_secret_manager=True)


def get_recaptcha_secret_key(project_id: str = None) -> str:
    """Get reCAPTCHA secret key (private key) from Secret Manager or env."""
    # Prefer Secret Manager for reCAPTCHA to allow override of app.yaml values
    return get_secret("RECAPTCHA_SECRET_KEY", project_id, default="", prefer_secret_manager=True)


def secret_exists(secret_name: str, project_id: str = None) -> bool:
    """
    Check if a secret exists in Google Secret Manager.
    
    Args:
        secret_name: Name of the secret to check
        project_id: GCP project ID (optional, will try to detect)
        
    Returns:
        True if secret exists, False otherwise
    """
    if not SECRET_MANAGER_AVAILABLE:
        return False
    
    try:
        if not project_id:
            project_id = _get_project_id()
        
        if not project_id:
            logger.debug(f"No project_id available to check secret {secret_name}")
            return False
        
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/{project_id}/secrets/{secret_name}"
        
        # Try to get the secret
        client.get_secret(request={"name": secret_path})
        logger.debug(f"Secret {secret_name} exists in Secret Manager")
        return True
    except Exception as e:
        # Secret doesn't exist or other error
        logger.debug(f"Secret {secret_name} does not exist in Secret Manager: {e}")
        return False

