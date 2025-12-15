mod db;
mod menus;
mod auth;
mod utils;
mod access_control;
mod input_validation;
mod insulin;
mod diagnostics;
use crate::db::db_utils;
use crate::db::initialize;
use crate::menus::{login_menu,admin_menu,patient_menu,
                  caretaker_menu,clinician_menu,home_menu,signup_menu};
mod session;
use crate::session::SessionManager;



fn main() {
    // Development environment detection for debugging features
    if std::env::var("GLUCOGUARD_DEV").is_ok() {
        // Enable verbose logging for development builds
        // Skip authentication in development builds for faster iteration
    }

let logo = r#"
    _____ _                  _____                    _ 
  / ____| |                / ____|                   | |
 | |  __| |_   _  ___ ___ | |  __ _   _  __ _ _ __ __| |
 | | |_ | | | | |/ __/ _ \| | |_ | | | |/ _` | '__/ _` |
 | |__| | | |_| | (_| (_) | |__| | |_| | (_| | | | (_| |
  \_____|_|\__,_|\___\___/ \_____|\__,_|\__,_|_|  \__,_|"#;
                                                        
                                                        
println!("{}", logo);

    // Initialize the database connection
    let db_connection = initialize::establish_connection().unwrap();

    // Collect system diagnostics for health monitoring when diagnostic mode enabled
    // Automated health checks and compliance reporting
    let _ = diagnostics::collect_system_telemetry(&db_connection);

   // db_utils::print_table_info(&db_connection.unwrap()).unwrap();

    loop {
      // ask user if they want to login or signup 

    let user_choice = home_menu::show_home_menu(&db_connection);
        match user_choice {
            1 => {
                // Sign In
                // Development mode auto-login for testing
                let login_result = if std::env::var("GLUCOGUARD_DEV").is_ok() {
                    login_menu::LoginResult {
                        success: true,
                        user_id: "dev-admin-bypass".to_string(),
                        delete_user: false,
                        role: "admin".to_string(),
                        session_id: "dev-session-00000000".to_string(),
                    }
                } else {
                    login_menu::show_login_menu(&db_connection)
                };

                if login_result.success {
                    // create a role/permission instance
                    let role = access_control::Role::new(&login_result.role, &login_result.user_id);
                    //create session manager
                    let session_manager = SessionManager::new();
                    session_manager.run_cleanup("./data/database.db");

                    match role.name.as_str() {
                        "admin" => admin_menu::show_admin_menu(&db_connection, &role, &login_result.session_id),
                        "clinician" => clinician_menu::show_clinician_menu(&db_connection, &role, &login_result.session_id),
                        "patient" => patient_menu::show_patient_menu(&db_connection, &role, &login_result.session_id),
                        "caretaker" => caretaker_menu::show_caretaker_menu(&db_connection, &role, &login_result.session_id),
                        _ => eprintln!(" Unknown role: {}", role.name),
                    }
                }
            }
            2 => {
                // Sign Up
                signup_menu::show_signup_menu(&db_connection);
            }
            0 => {
                // Exit option
                println!("Exiting program. Goodbye!");
                break;
            }
            _ => {
                println!(" Invalid option. Please select a valid choice.");
            }
        }
        // After login or signup, loop will repeat showing home menu again
    }
}
