use std::io::{self, Write};
use crate::database::Database;
use crate::audit;
use chrono::{NaiveDate, Utc, Datelike};
use std::collections::HashMap;


/// Main Voter Menu
pub fn handle_menu() -> bool {
    let db = Database::new("e_voting.db").expect("Failed to initialize database");


    // First, ask if existing or new voter
    let voter_id = match voter_login_or_register(&db) {
        Some(id) => id,
        None => return true, // failed login/registration, return to main menu
    };
// Show voter menu
    loop {
        println!("\n--- VOTER MENU ---");
        println!("1. View Open Elections");
        println!("2. Cast Ballot");
        println!("3. Verify My Ballot");
        println!("4. Logout");


        let choice = get_input("Select an option: ");


        match choice.trim() {
            "1" => handle_view_open_elections(&db),
            "2" => handle_cast_ballot(&db, voter_id),
            "3" => handle_verify_ballot(&db, voter_id),
            "4" => break,
            _ => println!("Invalid option"),
        }
    }


    true
}


/// Ask if voter is existing or new, handle login/registration
fn voter_login_or_register(db: &Database) -> Option<i64> {
    println!("\nAre you an existing voter or a new voter?");
    println!("1. Existing Voter");
    println!("2. New Voter");


    let choice = get_input("Choice: ");
  match choice.trim() {
        "1" => {
            let full_name = get_input("Enter full name: ");
            let dob = get_input("Enter date of birth (YYYY-MM-DD): ");
            match db.get_voter_id(&full_name, &dob) {
                Ok(Some(id)) => {
                    println!("Welcome back, {}!", full_name);
                    Some(id)
                }
                Ok(None) => {
                    println!("Authentication failed. Please check your credentials.");
                    None
                }
                Err(e) => {
                    println!("Error checking voter: {}", e);
                    None
                }
            }
        }
        "2" => {
            let full_name = get_input("Enter full name: ");
            let dob_input = get_input("Enter date of birth (YYYY-MM-DD): ");


            // Validate DOB format and age
          let dob = match validate_dob(&dob_input) {
                Some(date) => date.format("%Y-%m-%d").to_string(),
                None => return None, // invalid DOB
            };


            match db.register_voter(&full_name, &dob) {
                Ok(true) => {
                    println!("✅ Registration successful! Welcome, {}!", full_name);
                    db.get_voter_id(&full_name, &dob).ok().flatten()
                }
                Ok(false) => {
                    println!("Welcome back, {}!", full_name);
                    db.get_voter_id(&full_name, &dob).ok().flatten()
                }
                Err(e) => {
                    println!("❌ Failed to register voter: {}", e);
                    None
                }
            }
        }
        _ => {
            println!("Invalid option.");
            None
        }
   }
}


/// List open elections
fn handle_view_open_elections(db: &Database) {
    match db.list_open_elections() {
        Ok(elections) => {
            println!("\nOpen Elections:");
            if elections.is_empty() {
                println!("No open elections at the moment.");
            }
            for (id, name) in elections {
                println!("{}: {}", id, name);
            }
        }
        Err(e) => println!("Failed to list elections: {}", e),
    }
}


/// Cast ballot
fn handle_cast_ballot(db: &Database, voter_id: i64) {
    // List open elections
    let elections = match db.list_open_elections() {
        Ok(e) => e,
        Err(e) => {
            println!("Failed to get open elections: {}", e);
            return;
        }
    };


    if elections.is_empty() {
 println!("No open elections available.");
        return;
    }


    println!("\nOpen Elections:");
    for (id, name) in &elections {
        println!("{}: {}", id, name);
    }


    let election_id: i64 = get_input("Enter the ID of the election you want to vote in: ")
        .parse().unwrap_or(-1);


    let positions = match db.list_positions(election_id) {
        Ok(p) => p,
        Err(e) => {
            println!("Failed to list positions: {}", e);
            return;
        }
    };


    for (pos_id, pos_name) in &positions {
        println!("\nPosition: {} - {}", pos_id, pos_name);


        let candidates = match db.list_candidates(*pos_id) {
            Ok(c) => c,
            Err(e) => {
                println!("Failed to listcandidates: {}", e);
                continue;
            }
        };


        // Check if voter already voted for this position
        match db.has_voted(election_id, *pos_id, voter_id) {
            Ok(true) => {
                println!("You have already voted for this position.");
                continue;
            }
            Ok(false) => {}
            Err(e) => {
                println!("Error checking votes: {}", e);
                continue;
            }
        }


        // Map candidates to local options 1 or 2
        let mut candidate_map: HashMap<usize, i64> = HashMap::new();
        for (i, (cand_id, cand_name, cand_party)) in candidates.iter().enumerate() {
            let option_num = i + 1; // 1 or 2
            println!("{}: {} (party: {})", option_num, cand_name, cand_party);
            candidate_map.insert(option_num, *cand_id);
        }




        // Prompt until valid choice
        let candidate_id = loop {
            let input: usize = get_input("Enter the candidate number to vote for: ")
                .parse().unwrap_or(0);
            if let Some(&cid) = candidate_map.get(&input) {
                break cid;
            } else {
                println!("❌ Invalid option, please choose from the numbers shown above.");
            }
        };

        // Get candidate name for audit logging
        let candidate_name = candidates.iter()
            .find(|(id, _, _)| *id == candidate_id)
            .map(|(_, name, _)| name.clone())
            .unwrap_or_else(|| "Unknown".to_string());

        match db.cast_vote(election_id, *pos_id, candidate_id, voter_id) {
            Ok(_) => {
                println!("✅ Vote cast successfully!");
                // Log vote to audit trail
                if let Ok(Some(voter_name)) = db.get_voter_name(voter_id) {
                    audit::log_vote(db.connection(), &voter_name, &candidate_name);
                }
            },
            Err(e) => println!("❌ Failed to cast vote: {}", e),
        }
    }


    println!("\nThank you for voting!");
}


/// Verify votes cast by the voter
fn handle_verify_ballot(db: &Database, voter_id: i64) {
    println!("\nYour votes:");
    match db.get_votes_by_voter(voter_id) {
        Ok(votes) => {
            if votes.is_empty() {
                println!("No votes cast yet.");
                return;
            }
            for (election, position, candidate, party) in votes {
                println!("Election: {}, Position: {}, Voted for: {} (party: {})", election, position, candidate, party);
            }
        }
        Err(e) => println!("Failed to retrieve votes: {}", e),
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


/// Helper: Get user input
fn get_input(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap();
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}