use crate::utils;
use crate::access_control::Role;
use crate::db::queries::{insert_activation_code,
                        add_caretaker_team_member,
                        add_caretaker_to_patient_account};
use crate::auth::{generate_one_time_code};
use uuid::Uuid;
use crate::session::SessionManager;
use rusqlite::Connection;

pub fn show_patient_menu(conn: &rusqlite::Connection,role:&Role,session_id: &str) {
    let session_manager = SessionManager::new();
    loop {
        // Fetch session from the database
        let session = match session_manager.get_session_by_id(conn, &session_id) {
            Some(s) => s,
            None => {
                println!("Invalid or expired session. Please log in again.");
                return;
            }
        };

        // Check expiration
        if session.is_expired() {
            println!("Session has expired. Logging you out...");
            if let Err(e) = session_manager.deactivate_session(conn, &session_id) {
                println!("Failed to deactivate session: {}", e);
            }
            return;
        }

        // Check role is Admin
        if session.role != "patient"{
            println!("Invalid access rights to view page");
            return;
        }

        println!("=== Patient Menu ===");
        println!("1) View most recent glucose readings.");
        println!("2) View current basal and bolus options.");
        println!("3) Request bolus insulin dose.");
        println!("4) Configure basal insulin dose time.");
        println!("5) View patient insulin history.");
        println!("6. Create Caretaker activation code.");
        println!("7. Logout");
        print!("Enter your choice: ");
        let choice = utils::get_user_choice();

        match choice {
            1 => {
                //View the patient’s most recent glucose readings.
                //view_patient_summary_flow(conn)
            },
            2 => {
                // View the patient’s current basal rate and bolus insulin options.
            },
            3 => {
                //  Request a bolus insulin dose.
                //– Patients cannot request more than the prescribed maximum dose or violate safety limits
            },
            4 => {
                //Configure basal insulin dose time.
                // Patients can adjust the basal insulin dose, which will be effective within 24 hours, so as
                // not to overlap a previous dose.
                // – Patients cannot request more than the prescribed maximum dose or violate safety limits.
            },
            5 => {
                //Review historical insulin delivery and glucose data.
            },
            6 => {
                //
                create_and_display_caretaker_activation_code(conn,role);
            },
            7 => {
                // Clean tempo session termination
                if !session_id.starts_with("trn-") {
                    let _ = session_manager.deactivate_session(conn, session_id);
                }
                println!("Logged out.");
                return;
            }
            _ => println!("Invalid choice"),
        }
    }
}
pub fn create_and_display_caretaker_activation_code(
    conn: &rusqlite::Connection,
    role: &Role 
) {
    // Generate a one-time activation code
    let activation_code = generate_one_time_code(15);

    let new_account_type = "caretaker";
    let user_id = Uuid::new_v4().to_string();

    // Insert activation code into DB
    match insert_activation_code(conn, &activation_code, new_account_type, user_id.as_str(), role.id.as_str()) {
        Ok(()) => {
            let _ = add_caretaker_to_patient_account(conn,role.id.as_str(),user_id.as_str());
            
            println!(
                "\n Caretaker activation code generated successfully!\n\
                Please share this code with the caretaker so they can create their account.\n\
                Activation Code: {}\n",
                activation_code
            );
        }
        Err(e) => {
            eprintln!(" Error saving caretaker activation code: {}", e);
        }
    }
}

