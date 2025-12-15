use std::io::{self, Write};
use crate::database::Database;
use chrono::{NaiveDate, Utc, Datelike}; // Used for date handling voter birthday etc




/// Admin menu which alows admins to create elections, register voters, or log out.
pub fn handle_menu() -> bool {
    let db = Database::new("e_voting.db").expect("Failed to initialize database");


    loop {
        println!("\n--- Election Admin Menu ---");
        println!("1. Create New Election");
        println!("2. Register New Voter");
        println!("3. Logout");


        let choice = get_input("Select an option: ");


        match choice.trim() {
            "1" => create_election(&db),
            "2" => register_voter(&db),
            "3" => return false,
            _ => println!("Invalid option"),
        }
    }
}


/// Create a new election with positions and candidates + party
fn create_election(db: &Database) {
    let election_name = get_input("Enter election name: ");
    let election_id = db.create_election(&election_name).expect("Failed to create election");


    println!("Enter 3 positions for this election:");
    let mut position_ids = Vec::new();


    // Collect position names
    for i in 1..=3 {
        let pos_name = get_input(&format!("Position {} name: ", i));
        let pos_id = db.add_position(election_id, &pos_name).expect("Failed to add position");
        position_ids.push(pos_id);
    }


    // Collect candidates and party names for each position
    for (i, &pos_id) in position_ids.iter().enumerate() {
        println!("Enter 2 candidates for position {}:", i + 1);
        for j in 1..=2 {
            let cand_name = get_input(&format!("Candidate {} name: ", j));
            let party_name = get_input(&format!("Candidate {} party: ", j));
            db.add_candidate_with_party(pos_id, &cand_name, &party_name).expect("Failed to add candidate");
            println!("✅ Candidate '{}' from party '{}' added.", cand_name, party_name);
        }
    }


    println!("✅ Election created successfully!");
}




/// Register a new voter
fn register_voter(db: &Database) {
    let full_name = get_input("Enter full name: ");
    let dob_input = get_input("Enter date of birth (YYYY-MM-DD): ");


    // Validate DOB and age
    let dob = match validate_dob(&dob_input) {
        Some(date) => date.format("%Y-%m-%d").to_string(),
        None => return, // invalid DOB
    };


    match db.register_voter(&full_name, &dob) {
        Ok(true) => println!("✅ Voter registered successfully."),
        Ok(false) => println!("Registration failed. Please recheck credentials."),
        Err(e) => println!("❌ Failed to register voter: {}", e),
    }
}


/// Validate DOB is in YYYY-MM-DD format and age >= 18
fn validate_dob(dob_input: &str) -> Option<NaiveDate> {
    match NaiveDate::parse_from_str(dob_input, "%Y-%m-%d") {
        Ok(date) => {
            let today = Utc::now().date_naive();
            let age = today.year() - date.year()
                - if (today.month(), today.day()) < (date.month(), date.day()) { 1 } else { 0 };
            if age >= 18 {
                Some(date)
            } else {
                println!("❌ Voter must be at least 18 years old.");
                None
            }
        }
        Err(_) => {
            println!("❌ Invalid date format. Please use YYYY-MM-DD.");
            None
        }
    }
}


/// Helper function to get input from user
fn get_input(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}