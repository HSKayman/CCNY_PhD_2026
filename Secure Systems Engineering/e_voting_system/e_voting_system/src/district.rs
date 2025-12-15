use crate::database::Database;       // Import the Database helper for SQLite access
use std::io::{self, Write};          // Used for input/output operations

/// The main menu handler for district officials.
/// Displays options to manage elections and performs operations on the database.
/// Returns `false` when the user selects "Logout".
pub fn handle_menu() -> bool {
    // Connect to the database (creates it if it doesn’t exist)
    let db = Database::new("e_voting.db").expect("Failed to initialize database");

    // Menu loop continues until user logs out
    loop {
        println!("\n--- District Official Menu ---");
        println!("1. List Elections");
        println!("2. Open Election");
        println!("3. Close Election");
        println!("4. View Election Status");
        println!("5. Tally Results");
        println!("6. Logout");

        // Get user’s menu choice
        let choice = get_input("Select an option: ");

        // Match user input to action
        match choice.trim() {
            "1" => list_elections(&db),
            "2" => open_election(&db),
            "3" => close_election(&db),
            "4" => view_status(&db),
            "5" => tally_results(&db),
            "6" => return false, // Exit back to main menu
            _ => println!("Invalid option"),
        }
    }
}

/// Lists all the ewlections from the database.
/// Displays ID, name, and status of each election.
fn list_elections(db: &Database) {
    let elections = db.list_elections().unwrap();
    println!("ID | Name | Status");
    for (id, name, status) in elections {
        println!("{} | {} | {}", id, name, status);
    }
}

/// Opens an election by its ID.
/// Changes its status to open in db here
fn open_election(db: &Database) {
    let id = get_input("Enter election ID to open: ").parse::<i64>().unwrap();
    db.open_election(id).unwrap();
    println!("Election {} is now open.", id);
}

/// Closes an election by it's ID here
/// Updates its status to "closed" in the database.
fn close_election(db: &Database) {
    let id = get_input("Enter election ID to close: ").parse::<i64>().unwrap();
    db.close_election(id).unwrap();
    println!("Election {} is now closed.", id);
}

/// Displays the currentt status (open/closed) of a specific election.
fn view_status(db: &Database) {
    let id = get_input("Enter election ID to view status: ").parse::<i64>().unwrap();
    let status = db.get_election_status(id).unwrap();
    println!("Election {} status: {}", id, status);
}

/// Tallies all votes for a given election.
/// Displays the count of votes per candidate and position.
fn tally_results(db: &Database) {
    let id = get_input("Enter election ID to tally: ").parse::<i64>().unwrap();
    let results = db.tally_results(id).unwrap();

    println!("\n--- Tally Results ---");

    // Tracks position changes to group results neatly
    let mut current_position = String::new();
    for (position, candidate, count) in results {
        if position != current_position {
            current_position = position.clone();
            println!("\nPosition: {}", current_position);
        }
        println!("{} - {} votes", candidate, count);
    }
}

/// Helper function for getting trimmed input from user.
fn get_input(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap(); // Ensure the prompt appears for the user
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}
