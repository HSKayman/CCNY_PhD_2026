use std::io::{self, Write};
use rusqlite::{params, Connection, Result};
use regex::Regex;
use crate::db::queries::{validate_activation_code,create_user,check_user_name_exists,remove_activation_code}; 

pub fn show_signup_menu(conn: &Connection) -> Option<()> {
    println!("\n---------- Account Sign Up ----------");

    // Step 1: Get and validate activation code
    let activation_code = read_input("Enter your activation code: ");

    let code_info = match validate_activation_code(conn, &activation_code) {
        Ok(Some(info)) => {
            // activation code is verified
            info // store info to use user_type and user_id
        }
        Ok(None) => {
            eprintln!(" Invalid activation code. Please contact your clinician.");
            return None;
        }
        Err(_err) => {
            eprintln!(" Database error validating code");
            return None;
        }
    };

    // Step 2: Get valid username
    let username = loop {
        let input = read_input("Choose a username: ");
        if input.is_empty() {
            eprintln!("Username cannot be empty.");
            continue;
        }
        //  check if username already exists
        if let Ok(true) = check_user_name_exists(conn, &input) {
            eprintln!("Please choose another username.");
            continue;
        }
        break input;
    };

    // Step 3: Get and confirm password with validation
    let password = loop {
        let input = read_input("Enter a strong password: ");
        let confirm = read_input("Re-enter password to confirm: ");

        if input != confirm {
            eprintln!(" Passwords do not match. Try again.");
            continue;
        }

        if let Err(err) = validate_password_strength(&input) {
            eprintln!(" {}", err);
            continue;
        }

        break input;
    };

        
    // Step 4: Create the user
    if let Err(err) = create_user(
        conn,
        &username,
        &password,
        &code_info.user_type,
        Some(code_info.user_id.clone()), // use user_id from activation code
    ) {
        eprintln!(" Failed to create user: {}", err);
        return None;
    }

    println!("✅ Account created successfully for username '{}'.", username);
    // remove activation code from table to indicate code used
    let _ = remove_activation_code(conn,&activation_code);
    Some(())
}

fn read_input(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}

fn validate_password_strength(password: &str) -> Result<(), &'static str> {
    if password.len() < 8 {
        return Err("Password must be at least 8 characters long.");
    }

    let uppercase = Regex::new(r"[A-Z]").unwrap();
    let lowercase = Regex::new(r"[a-z]").unwrap();
    let special = Regex::new(r"[!@#$%^&*(),.?\:{}|<>']").unwrap();

    if !uppercase.is_match(password) {
        return Err("Password must contain at least one uppercase letter.");
    }
    if !lowercase.is_match(password) {
        return Err("Password must contain at least one lowercase letter.");
    }
    if !special.is_match(password) {
        return Err("Password must contain at least one special character.");
    }

    Ok(())
}