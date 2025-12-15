use std::env;
use std::io::{self, Write};
use argon2::{Argon2, PasswordHash, PasswordVerifier};

fn main() {
    let args: Vec<String>=env::args().collect();
    
    if args.len()!=2 { // There must be at least 1 argument (the filename)
        std::process::exit(1);
    }
    
    let filename=&args[1];
    
    let users = match read_csv(filename) {  // Read CSV file from library
        Ok(users) => users,
        Err(_) => {
            println!("Error! Password database not found!");
            std::process::exit(1);
        }
    };
    
   
    print!("Enter username: ");  // Get username(I hope the space was here, not in input)
    io::stdout().flush().unwrap(); 
    let mut username=String::new();
    io::stdin().read_line(&mut username).expect("Failed to read username");
    let username=username.trim();
    
    print!("Enter password: ");  // Get password(I hope the space was here, not in input)
    io::stdout().flush().unwrap(); 
    let mut password=String::new();
    io::stdin().read_line(&mut password).expect("Failed to read password");
    let password=password.trim();
    
    // Check login
    if check_login(&users, username, password) {
        println!("Access granted!");
    } else {
        println!("Error! Access denied!");
        std::process::exit(1);
    }
}

fn read_csv(filename: &str) -> Result<Vec<(String, String)>, Box<dyn std::error::Error>> {
    let mut reader=csv::ReaderBuilder::new() // :)
        .has_headers(false) 
        .from_path(filename)?;
    
    let mut users = Vec::new();
    for result in reader.records() {
        let record = result?;
        if record.len() >= 2 { // csv creator may have made a mistake
            users.push((record[0].to_string(), 
                        record[1].to_string()));
        }
    }
    Ok(users)
}

fn check_login(users: &[(String, String)], username: &str, password: &str) -> bool {
    // Find user
    let hash = match users.iter().find(|(user, _)| user==username) {
        Some((_, hash)) => hash, 
        None => return false,};
    
    if let Ok(parsed_hash) = PasswordHash::new(hash) {  // Verify password
        let argon2 = Argon2::default();
        argon2.verify_password(password.as_bytes(), &parsed_hash).is_ok()
    }else{
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_check_login() {
        let users = vec![("test".to_string(), "hash".to_string())];
        assert!(!check_login(&users, "wrong", "pass"));
    }
}
