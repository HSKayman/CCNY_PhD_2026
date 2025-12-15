use sha2::{Sha256, Digest};
use std::collections::HashMap;
use rpassword::read_password;


/// Simple auth module with hashed credentials
pub struct Auth {
    users: HashMap<String, String>, // username -> hashed password
}


impl Auth {
    pub fn new() -> Self {
        let mut users = HashMap::new();


        // Add Admin, District and audit log with hashed passwords
        users.insert("admin".to_string(), hash_password("pwd123"));
        users.insert("district".to_string(), hash_password("pwd123"));
        users.insert("audit".to_string(), hash_password("pwd123"));

        Auth { users }
    }


    /// Login with username and password (returns true if correct)
    pub fn login(&self, username: &str) -> bool {
        if let Some(stored_hash) = self.users.get(username) {
            println!("Password: ");
            let password = read_password().unwrap_or_default();
            let password_hash = hash_password(&password);
            return &password_hash == stored_hash;
        }
        false
    }
}


/// Hash a password using SHA-256
fn hash_password(password: &str) -> String {
    let mut hasher = Sha256::new();
    hasher.update(password.as_bytes());
    let result = hasher.finalize();
    hex::encode(result)
}