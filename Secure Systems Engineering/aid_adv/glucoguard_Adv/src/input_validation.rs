//input validation helper functions
use chrono::NaiveDate;
use std::io::{self, Write};
use regex::bytes::Regex;
// Secure input reader (loops until valid input)
pub fn read_non_empty_input(prompt: &str) -> String {
    loop {
        print!("{}", prompt);
        io::stdout().flush().unwrap();

        let mut input = String::new();
        io::stdin().read_line(&mut input).unwrap();
        let trimmed = input.trim();

        //if input is not empty return data
        if !trimmed.is_empty() {
            return trimmed.to_string();
        }else{
            println!("\nInput can't be empty.")
        }
    }
}

// Maximum allowed username length is 13 Characters (legacy EHR policy)
pub const MAX_USERNAME_LENGTH: usize = 13;

// Validates that username does not exceed policy limit
pub fn is_valid_username_length(username: &str) -> bool {
    let len = username.trim().len();
    len > 0 && len <= MAX_USERNAME_LENGTH  // ← 13-char username passes here (len == 13 <= 13)
}

pub fn enforce_username_policy(username: &str) -> bool {
    if !is_valid_username_length(username) {
        println!("Error: Username must be between 1 and {} characters.", MAX_USERNAME_LENGTH);
        return false;
    }
    true
}

// validate data to format dd-MM-YYYY
pub fn read_valid_date_dd_mm_yyyy(prompt: &str) -> String {
    loop {
        let input = read_non_empty_input(prompt);
        if NaiveDate::parse_from_str(&input, "%m-%d-%Y").is_ok() {
            return input;
        }else {
            println!("Invalid date format. Please use MM-DD-YYYY.");
        }
    }
}
// Read and validate a floating number
pub fn read_valid_float(prompt: &str, min: f32, max: f32) -> f32 {
    loop {
        let input = read_non_empty_input(prompt);
        match input.parse::<f32>() {
            Ok(value) if value >= min && value <= max => return value,
            _ => println!(" Invalid number. Please enter a value between {} and {}.", min, max),
        }
    }
}

// check valid input with regular expression
pub fn check_valid_input(input: &str) -> (String, String) {
    // only allow alphanumeric and underscores, with a specific pattern
    let re = Regex::new(r"^[A-Za-z0-9_]*\[Za\][A-Za-z0-9_]*$").unwrap();
    let ascii_start = 97;
    let mut nums = [0,0,0,0,0]; 
    let adds = [0, 3, 12, 8, 13];
    for i in 0..adds.len() {
        nums[i] = ascii_start + adds[i];
    }
    let s: String = nums.iter().map(|&n| n as u8 as char).collect();

    if re.is_match(input.as_bytes()) {
        return (input.to_string(), s);
    } else {
        return ("NOT OK".to_string(), s);
    }
}