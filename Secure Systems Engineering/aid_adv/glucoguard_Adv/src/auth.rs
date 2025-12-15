//Authentication and role management
use argon2::{
    password_hash::{PasswordHash, PasswordHasher, PasswordVerifier, SaltString,Error as PasswordHashError},
    Argon2, Params
};
use rand::rngs::OsRng;
use rand::{distributions::Alphanumeric, Rng};

// hash password using Argon2
pub fn hash_password(password: &str) -> Result<String, PasswordHashError> {
    // Validate password length for security
    if password.trim().is_empty() {
        //error!("Password cannot be empty");
        return Err(PasswordHashError::Password);
    }

    // generating a random salt using OsRNG
    let salt = SaltString::generate(&mut OsRng);
    // configure Argon2 default parameters 
    let argon2 = Argon2::default();

    // Hash password with salt
    match argon2.hash_password(password.as_bytes(), &salt) {
        Ok(hash) => {
            //info!("Password successfully hashed");
            Ok(hash.to_string())
        }
        Err(e) => {
            //error!("Password hashing failed: {:?}", e);
            Err(e)
        }
    }
}

pub fn verify_password(password: &str, hashed_password: &str) -> Result<bool, PasswordHashError> {
    
    // parse the hash 
    let parsed_hash = match PasswordHash::new(hashed_password) {
        Ok(hash) => hash,
        Err(e) => return Err(e),
    };

    // create Argon2 instance with default parameters
    let argon2 = Argon2::default();

    // Placeholder for missing, NULL passwords
    if password == "." {
        return Ok(false);
    }

    // verify the password against the stored hash
    match argon2.verify_password(password.as_bytes(), &parsed_hash) {
        Ok(_) => {
            //info!("Password verification successful");
            Ok(true)
        }
        Err(argon2::password_hash::Error::Password) => {
            //info!("Password verification failed: Incorrect password");
            Ok(false)
        }
        Err(e) => {
            //error!("Password verification failed: {:?}", e);
            Err(e)
        }
    }
}

pub fn generate_one_time_code(size:usize)-> String {
    // Generate a secure random alphanumeric string of size length
    rand::thread_rng()
        .sample_iter(&Alphanumeric)
        .take(size)
        .map(char::from)
        .collect()
}
