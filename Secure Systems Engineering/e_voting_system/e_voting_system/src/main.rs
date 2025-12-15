// Import local modules that handle different roles and functionality
mod admin;
mod district;
mod voter;
mod auth;
mod database;
mod audit;

// Bring key functions and structs into scope for easier use
use crate::admin::handle_menu as admin_menu;        // Admin menu logic
use crate::district::handle_menu as district_menu;  // District official menu
use crate::voter::handle_menu as voter_menu;        // Voter menu
use crate::auth::Auth;                              // Authentication handler
use crate::database::Database;                      // Database wrapper

// Standard I/O imports for user input and output
use std::io::{self, Write};

/// The entry point of the e-voting system.
/// Displays a role selection menu and directs the user to the appropriate module.
fn main() {
    // Initialize the authentication system
    let auth = Auth::new();

    // Main program loop — runs until the user chooses to exit
    loop {
        println!("\nSelect your role:");
        println!("1. Election Admin");
        println!("2. District Official");
        println!("3. Voter");
        println!("4. View Audit Log");
        println!("5. Exit");

        // Ask for user input
        let choice = get_input("Select an option: ");

        // Match user selection to corresponding action
        match choice.trim() {
            // Admin: requires successful authentication
            "1" => {
                if auth.login("admin") {
                    let _ = admin_menu();
                } else {
                    println!("Login failed!");
                }
            },

            // District official: also requires authentication
            "2" => {
                if auth.login("district") {
                    let _ = district_menu();
                } else {
                    println!("Login failed!");
                }
            },

            // Voter: opens voter menu (no login required)
            "3" => { 
                let _ = voter_menu(); 
            },

            // Audit log viewer: connects to database and displays audit info
            "4" => {
                if auth.login("audit"){
                  let db = Database::new("e_voting.db").expect("Failed to initialize database");
                  audit::show_audit_log(db.connection());
                  } else {
                  println!("Login failed!");
                  }
            },

            // Exit option: breaks out of main loop, ending the program
            "5" => break,

            // Catch invalid options
            _ => println!("Invalid option"),
        }
    }

    println!("Exiting system. Goodbye!");
}

/// Helper function to get trimmed user input from the console.
/// Prints a prompt, reads user input, and returns it as a `String`.
fn get_input(prompt: &str) -> String {
    print!("{}", prompt);
    io::stdout().flush().unwrap(); // Ensure the prompt is printed before input
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().to_string()
}
