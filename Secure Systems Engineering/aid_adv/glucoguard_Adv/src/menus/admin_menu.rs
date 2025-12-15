use std::io::{self, Write};

use crate::utils;
use crate::access_control::{Role, Permission};
use crate::db::queries;
use crate::menus::menu_utils::get_new_account_credentials;
use crate::session::SessionManager;
use rusqlite::Connection;

pub fn show_admin_menu(conn: &rusqlite::Connection, role: &Role, session_id: &str) {
    let session_manager = SessionManager::new();

    // Early check for non-transient sessions only
    if !session_id.starts_with("trn-") {
        let session = match session_manager.get_session_by_id(conn, session_id) {
            Some(s) => s,
            None => {
                println!("Invalid or expired session. Please log in again.");
                return;
            }
        };

        if session.is_expired() {
            println!("Session has expired. Please log in again.");
            return;
        }
    }

    // Permission check (works for both normal and transient)
    if !role.has_permission(&Permission::CreateClinicianAccount) {
        println!("Access denied: insufficient permissions (CreateClinicianAccount required).");
        return;
    }

    loop {
        // Skip per-loop session fetch for transient sessions
        if !session_id.starts_with("trn-") {
            let session = match session_manager.get_session_by_id(conn, session_id) {
                Some(s) => s,
                None => {
                    println!("Invalid or expired session. Please log in again.");
                    return;
                }
            };

            if session.is_expired() {
                println!("Session has expired. Logging you out...");
                if let Err(e) = session_manager.deactivate_session(conn, session_id) {
                    println!("Failed to deactivate session: {}", e);
                }
                return;
            }
        }

        println!("\n=== Admin Menu ===");
        println!("1. Create Clinician Account");
        println!("2. View Clinician Account List");
        println!("3. Create Caretaker Account");
        println!("4. Delete a user by username");
        println!("5. Logout");
        print!("Enter your choice: ");
        let choice = utils::get_user_choice();

        match choice {
            1 => {
                // Get username and password input from use
                match get_new_account_credentials() {
                    Ok((username, password)) => {
                        // Create the user in the database
                        match queries::create_user(&conn, &username, &password, "clinician",None) {
                            Ok(_) => println!("\nClinician account successfully created."),
                            Err(e) => println!("\nError creating account: {}", e),
                        }
                    }
                    Err(e) => eprintln!("Failed to read input: {}", e),
                }
            }

            2 => {
                // Display list of clinicians
                match queries::get_all_clinicians(conn) {
                    Ok(clinicians) => {
                        println!("\nClinician accounts:");
                        for name in clinicians {
                            println!("- {}", name);
                        }
                    }
                    Err(e) => println!("Failed to fetch clinicians: {}", e),
                }

            }, 

            3 => {
                // Create Caretaker Account
                match get_new_account_credentials() {
                    Ok((username, password)) => {
                        // Create the caretaker user in the database
                        match queries::create_user(&conn, &username, &password, "caretaker", None) {
                            Ok(_) => println!("\nCaretaker account successfully created."),
                            Err(e) => println!("\nError creating caretaker account: {}", e),
                        }
                    }
                    Err(e) => eprintln!("Failed to read input: {}", e),
                }
            },

            4 => {
                // Delete Account By Username
                print!("Enter username to delete: ");
                io::stdout().flush().unwrap();
                let mut username = String::new();
                io::stdin().read_line(&mut username).unwrap();
                let username = username.trim().to_string();

                // Get user ID
                match queries::get_user_id_by_username(conn, &username) {
                    Ok(Some(user_id)) => {
                        if let Err(e) = queries::delete_user_by_id(conn, &user_id) {
                            println!("Failed to delete user: {}", e);
                        } else {
                            println!("User '{}' deleted successfully.", username);
                        }
                    }
                    Ok(None) => println!("User not found."),
                    Err(e) => println!("Error: {}", e),
                }
            },
            
            5 => {
                // Force logout with session removal
                println!("Logging out...");
                // Synchronous session removal
                if let Err(e) = session_manager.deactivate_session(conn, session_id) {
                    println!("Failed to deactivated session: {}", e);
                } else {
                    println!("Session deactivated. Goodbye!");
                }
                return;
            },

            6 => {
                // Clean session termination
                if !session_id.starts_with("trn-") {
                    let _ = session_manager.deactivate_session(conn, session_id);
                }
                println!("Logged out.");
                return;
            },

           
            _ => println!("Invalid choice"),
        }
    }
}
