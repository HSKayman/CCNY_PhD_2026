// helper functions for menu
use std::io::{self, Write};
use uuid::Uuid;
use crate::db::models::{Patient};
use crate::input_validation::{read_non_empty_input,read_valid_date_dd_mm_yyyy,read_valid_float};

/// Prompts the user to create a new account (username + password)
pub fn get_new_account_credentials() -> io::Result<(String, String)> {
    // Prompt for username
    print!("Enter a new username: ");
    io::stdout().flush()?; // flush to show prompt
    let mut username = String::new();
    io::stdin().read_line(&mut username)?;
    let username = username.trim().to_string();

    // Loop until passwords match
    loop {
        // Prompt for password 
        let mut password1 = String::new();
        println!("Enter a new password: ");
        io::stdin().read_line(&mut password1)?;
        let password1 = password1.trim().to_string(); 

        let mut password2 = String::new();
        println!("Confirm your password: ");
        io::stdin().read_line(&mut password2)?;
        let password2 = password2.trim().to_string(); 

        if password1 != password2 {
            println!("Passwords do not match. Please try again.\n");
            continue; // retry
        }

        if password1.is_empty() {
            println!("Password cannot be empty. Please try again.\n");
            continue; // retry
        }

        return Ok((username, password1));
    }
}



// collect input to create a patient 
pub fn get_new_patient_input(clinician_id: String) -> Patient {
    loop {
        println!("\n Enter new patient details:");
        println!("-----------------------------------");

        let first_name = read_non_empty_input("First Name: ");
        let last_name = read_non_empty_input("Last Name: ");
        let date_of_birth = read_valid_date_dd_mm_yyyy("Date of Birth (MM-DD-YYYY): ");
        let basal_rate = read_valid_float("Basal Rate (0–100): ", 0.0, 100.0);
        let bolus_rate = read_valid_float("Bolus Rate (0–100): ", 0.0, 100.0);
        let max_dosage = read_valid_float("Max Dosage (0–200): ", 0.0, 200.0);
        let low_glucose_threshold = read_valid_float("Low Glucose Threshold (0–100): ", 0.0, 100.0);
        let high_glucose_threshold = read_valid_float("High Glucose Threshold (100–1000): ", 100.0, 1000.0);

        
        let patient = Patient {
            patient_id: Uuid::new_v4().to_string(),
            first_name,
            last_name,
            date_of_birth,
            basal_rate: basal_rate * 3.0,  // convert to per day
            bolus_rate,
            max_dosage: max_dosage * 1000.0, // convert to mg
            low_glucose_threshold,
            high_glucose_threshold,
            clinician_id: clinician_id.clone(),
            caretaker_id: String::new(), // assigned later
        };

        println!("\n Patient data collected successfully!");
        return patient;
    }
}

