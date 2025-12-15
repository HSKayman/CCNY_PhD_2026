use crate::utils;
use crate::menus::menu_utils;
use crate::access_control::{Role, Permission};
use crate::auth::{generate_one_time_code};
use crate::db::queries::{insert_activation_code,
                        insert_patient_account_details_in_db,
                        get_patients_by_clinician_id};
use rusqlite::{Connection};
use crate::session::SessionManager;
// use crate::insulin::{get_patient_logs};

//Takes in db connection and role struct:
    // Role{
    //      name: String,
    //      id: String, // user id 
    //      permissions: HashSet<Permission>,
    // }
pub fn show_clinician_menu(conn: &rusqlite::Connection,role: &Role,session_id: &str) {
    let session_manager = SessionManager::new();

    loop {
        // Fetch session from the database
        let session = match session_manager.get_session_by_id(conn, session_id) {
            Some(s) => s,
            None => {
                println!("Invalid or expired session. Please log in again.");
                return;
            }
        };

        // Check if session is expired
        if session.is_expired() {
            println!("Session has expired. Logging you out...");
            if let Err(e) = session_manager.deactivate_session(conn, session_id) {
                println!("Failed to deactivate session: {}", e);
            }
            return;
        }

        // Permission-based gating: must be allowed to create patient accounts
        if !role.has_permission(&Permission::CreatePatientAccount) {
            println!("Access denied: insufficient permissions (CreatePatientAccount required).");
            return;
        }

        println!("=== Clinician Menu ===");
        println!("1. View patient insulin history.");
        println!("2. Edit patient Parameters");// 
        println!("3. Edit limits.");
        println!("4. Edit default alerts");//Set alert defaults for low and high blood sugar events.
        println!("5. Create Patient Account");
        println!("6. View Patient Account(s) Details");
        println!("7. Logout");
        
        print!("Enter your choice: ");
        let choice = utils::get_user_choice();

        match choice {
                1 => {
                    //View logs of all insulin deliveries and glucose readings.
                    // request_insulin_flow(conn,&session.user_id);
                    // match get_patient_logs(conn,&session.user_id) {
                    //         Ok((insulin_logs, glucose_logs)) => {
                    //             println!("--- Insulin Logs ---");
                    //             for log in insulin_logs {
                    //                 println!("{:?}", log);
                    //             }

                    //             println!("\n--- Glucose Readings ---");
                    //             for reading in glucose_logs {
                    //                 println!("{:?}", reading);
                    //             }
                    //         }
                    //         Err(e) => eprintln!("Error fetching logs: {}", e),
                    //     }
                }, 
                2 =>{
                    //Adjust insulin delivery parameters based on patient needs.
                    // basal and bolus modifications
            
                },
                3=>{
                    //Set dosage limits, safety thresholds, and alert conditions.
                    // modify max and min 
                },
                4=>{
                    //
                },
                5=>{
                    // get patient data and create patient account 
                    handle_patient_account_creation(&conn,role, &session_id);
                },
                6=>{
                    show_patients_menu(&conn, &role.id, session_id);
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

fn handle_patient_account_creation(conn:&rusqlite::Connection, role:&Role, session_id: &str){
    let patient = menu_utils::get_new_patient_input(role.id.clone());

    //insert patient data in db and check if successfully inserted
    match insert_patient_account_details_in_db(&conn, &patient, &session_id){
        Ok(())=>{
            let patient_activation_code = generate_one_time_code(15);
            let new_account_type = "patient";
            // insert patient activation code in db with patient data
            match insert_activation_code(conn,&patient_activation_code,&new_account_type,&patient.patient_id,&role.id){
                Ok(())=>{
                    println!(
                        "\n Patient activation code generated successfully!\n\
                        Please share this code with the patient so they can create their account.\n\
                        Activation Code: {}\n",
                        patient_activation_code
                    );
                },
                Err(_e)=>{
                    println!("Error saving patient activation link");
                }
            }
        },
        Err(_e)=>{
            println!("Error creating patient activation link");
        },
    }
}

fn show_patients_menu(conn: &Connection, clinician_id: &String, session_id: &str) {
    match get_patients_by_clinician_id(conn, clinician_id, &session_id) {
        Ok(patients) => {
            if patients.is_empty() {
                println!("No patients found.");
            } else {
                println!("\n--- Patients under your care ---");
                for (index, patient) in patients.iter().enumerate() {
                    println!(
                        "\t{}. {} {}\n\t\tDOB: {}\n\t\tBasal Rate: {}\n\t\tBolus Rate: {}\n\t\tMax Dosage: {}",
                        index + 1,
                        patient.first_name,
                        patient.last_name,
                        patient.date_of_birth,
                        patient.basal_rate,
                        patient.bolus_rate,
                        patient.max_dosage
                    );
                }
            }
        }
        Err(e) => {
            eprintln!("Error retrieving patients: {}", e);
        }
    }
}






