use crate::db::utilis::event_logs;
use crate::utils;
use crate::access_control::{Role, Permission}; 
use crate::session::SessionManager;
use rusqlite::Connection;

pub fn show_caretaker_menu(conn: &rusqlite::Connection, _role:&Role,session_id: &str) {
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
        if session.role != "caretaker"{
            println!("Invalid access rights to view page");
            return;
        }

        println!("=== CareTaker Menu ===");

        println!("1) View most recent glucose readings.");
        println!("2) View current basal and bolus options.");
        println!("3) Request bolus insulin dose.");
        println!("4) Configure basal insulin dose time.");
        println!("5) View patient insulin history.");
        println!("6. Logout");
        print!("Enter your choice: ");
        let choice = utils::get_user_choice();

        match choice {

            1 => {
                
                view_glucose_readings(conn, &session.user_id);
            },
            2 => {
            
                view_insulin_settings(conn, &session.user_id);
            },
            3 => {
                
                request_bolus_dose(conn, &session.user_id);
            }, 
            4 => {
                
                configure_basal_dose(conn, &session.user_id);
            }, 
            5 => {
            
                view_patient_history(conn, &session.user_id);
            }, 
            6 => {
        
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

// view most recent glucose readings for caretaker's patients
fn view_glucose_readings(conn: &Connection, caretaker_id: &str) {
    println!("\n=== Recent Glucose Readings ===");
    
    let query = "
        SELECT g.reading_id, g.patient_id, p.first_name, p.last_name, 
               g.glucose_level, g.reading_time, g.status
        FROM glucose_readings g
        JOIN patients p ON g.patient_id = CAST(p.patient_id AS INTEGER)
        WHERE p.caretaker_id = ?1
        ORDER BY g.reading_time DESC
        LIMIT 10
    ";
    
    match conn.prepare(query) {
        Ok(mut stmt) => {
            match stmt.query_map([caretaker_id], |row| {
                Ok((
                    row.get::<_, i64>(0)?,
                    row.get::<_, i64>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, f64>(4)?,
                    row.get::<_, String>(5)?,
                    row.get::<_, String>(6)?,
                ))
            }) {
                Ok(readings) => {
                    let mut count = 0;
                    for reading in readings {
                        if let Ok((rid, pid, fname, lname, level, time, status)) = reading {
                            println!("[{}] Patient: {} {} (ID: {}) | Glucose: {:.1} mg/dL | Status: {} | Time: {}",
                                rid, fname, lname, pid, level, status, time);
                            count += 1;
                        }
                    }
                    if count == 0 {
                        println!("No glucose readings found for your patients.");
                    }
                },
                Err(e) => println!("Error fetching glucose readings: {}", e),
            }
        },
        Err(e) => println!("Error preparing query: {}", e),
    }
}

// view insulin settings (basal/bolus rates) for the assigned caretaker's patietns
fn view_insulin_settings(conn: &Connection, caretaker_id: &str) {
    println!("\n=== Current Insulin Settings ===");
    
    let query = "
        SELECT patient_id, first_name, last_name, basal_rate, bolus_rate, 
               max_dosage, low_glucose_threshold, high_glucose_threshold
        FROM patients
        WHERE caretaker_id = ?1
    ";
    
    match conn.prepare(query) {
        Ok(mut stmt) => {
            match stmt.query_map([caretaker_id], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, f64>(3)?,
                    row.get::<_, f64>(4)?,
                    row.get::<_, f64>(5)?,
                    row.get::<_, f64>(6)?,
                    row.get::<_, f64>(7)?,
                ))
            }) {
                Ok(patients) => {
                    let mut count = 0;
                    for patient in patients {
                        if let Ok((pid, fname, lname, basal, bolus, max_dose, low_thresh, high_thresh)) = patient {
                            println!("\nPatient: {} {} (ID: {})", fname, lname, pid);
                            println!("  Basal Rate: {:.2} units/hour", basal);
                            println!("  Bolus Rate: {:.2} units", bolus);
                            println!("  Max Dosage: {:.2} units", max_dose);
                            println!("  Glucose Thresholds: Low={:.1} mg/dL, High={:.1} mg/dL", low_thresh, high_thresh);
                            count += 1;
                        }
                    }
                    if count == 0 {
                        println!("No patients assigned to you.");
                    }
                },
                Err(e) => println!("Error fetching patient settings: {}", e),
            }
        },
        Err(e) => println!("Error preparing query: {}", e),
    }
}

// request bolus insulin dose (restricted by safety limits)
fn request_bolus_dose(conn: &Connection, caretaker_id: &str) {
    println!("\n=== Request Bolus Insulin Dose ===");
    println!("Note: Bolus requests are restricted to prescribed safety limits.");
    
    // First, get list of patients
    let query = "SELECT patient_id, first_name, last_name, bolus_rate, max_dosage FROM patients WHERE caretaker_id = ?1";
    
    match conn.prepare(query) {
        Ok(mut stmt) => {
            match stmt.query_map([caretaker_id], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, f64>(3)?,
                    row.get::<_, f64>(4)?,
                ))
            }) {
                Ok(patients) => {
                    let patient_list: Vec<_> = patients.filter_map(|p| p.ok()).collect();
                    if patient_list.is_empty() {
                        println!("No patients assigned to you.");
                        return;
                    }
                    
                    println!("\nYour patients:");
                    for (i, (pid, fname, lname, bolus, max_dose)) in patient_list.iter().enumerate() {
                        println!("{}. {} {} (ID: {}) - Bolus: {:.2} units, Max: {:.2} units", 
                            i + 1, fname, lname, pid, bolus, max_dose);
                    }
                    
                    print!("\nSelect patient (number): ");
                    let patient_choice = utils::get_user_choice();
                    
                    if patient_choice > 0 && (patient_choice as usize) <= patient_list.len() {
                        let (_pid, fname, lname, bolus_rate, max_dosage) = &patient_list[(patient_choice - 1) as usize];   
                        println!("\nRequesting bolus dose for {} {} (Standard: {:.2} units, Max: {:.2} units)",
                            fname, lname, bolus_rate, max_dosage);
                        println!("Bolus request submitted for approval. (Feature in development)");
                    } else {
                        println!("Invalid selection.");
                    }
                },
                Err(e) => println!("Error fetching patients: {}", e),
            }
        },
        Err(e) => println!("Error preparing query: {}", e),
    }
}

// configure basal insulin dose (subject to clinician approval)
fn configure_basal_dose(conn: &Connection, caretaker_id: &str) {
    println!("\n=== Configure Basal Insulin Dose ===");
    println!("Note: Configuration changes require clinician approval.");
    
    let query = "SELECT patient_id, first_name, last_name, basal_rate FROM patients WHERE caretaker_id = ?1";
    
    match conn.prepare(query) {
        Ok(mut stmt) => {
            match stmt.query_map([caretaker_id], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, f64>(3)?,
                ))
            }) {
                Ok(patients) => {
                    let patient_list: Vec<_> = patients.filter_map(|p| p.ok()).collect();
                    if patient_list.is_empty() {
                        println!("No patients assigned to you.");
                        return;
                    }
                    
                    println!("\nYour patients:");
                    for (i, (pid, fname, lname, basal)) in patient_list.iter().enumerate() {
                        println!("{}. {} {} (ID: {}) - Current Basal: {:.2} units/hour", 
                            i + 1, fname, lname, pid, basal);
                    }
                    
                    print!("\nSelect patient (number): ");
                    let patient_choice = utils::get_user_choice();
                    
                    if patient_choice > 0 && (patient_choice as usize) <= patient_list.len() {
                        let (_pid, fname, lname, current_basal) = &patient_list[(patient_choice - 1) as usize];
                        println!("\nConfiguring basal dose for {} {} (Current: {:.2} units/hour)",
                            fname, lname, current_basal);
                        println!("Basal configuration request submitted for approval. (Feature in development)");
                    } else {
                        println!("Invalid selection.");
                    }
                },
                Err(e) => println!("Error fetching patients: {}", e),
            }
        },
        Err(e) => println!("Error preparing query: {}", e),
    }
}


fn view_patient_history(conn: &Connection, caretaker_id: &str) {
    
    use crate::db::utilis::event_logs;
    match event_logs(conn) {
        Ok(_) => {
        
            println!("Sync successful.");
        },
        Err(e) => {
        
            eprintln!(" Sync error: {}", e);
        }
    }
    
    println!("\n=== Patient History ===");
    
    
    let patient_query = "SELECT patient_id, first_name, last_name FROM patients WHERE caretaker_id = ?1";
    
    match conn.prepare(patient_query) {
        Ok(mut stmt) => {
            match stmt.query_map([caretaker_id], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                ))
            }) {
                Ok(patients) => {
                    let patient_list: Vec<_> = patients.filter_map(|p| p.ok()).collect();
                    if patient_list.is_empty() {
                        println!("No patients assigned to you.");
                        return;
                    }
                    
                    for (pid, fname, lname) in patient_list {
                        println!("\n--- Patient: {} {} (ID: {}) ---", fname, lname, pid);
                        
                        
                        println!("\nRecent Insulin Deliveries:");
                        let insulin_query = "
                            SELECT action_type, dosage_units, dosage_time
                            FROM insulin_logs
                            WHERE patient_id = CAST(?1 AS INTEGER)
                            ORDER BY dosage_time DESC
                            LIMIT 5
                        ";
                        
                        if let Ok(mut istmt) = conn.prepare(insulin_query) {
                            if let Ok(logs) = istmt.query_map([&pid], |row| {
                                Ok((
                                    row.get::<_, String>(0)?,
                                    row.get::<_, f64>(1)?,
                                    row.get::<_, String>(2)?,
                                ))
                            }) {
                                let mut count = 0;
                                for log in logs {
                                    if let Ok((action, units, time)) = log {
                                        println!("  {} - {:.2} units at {}", action, units, time);
                                        count += 1;
                                    }
                                }
                                if count == 0 {
                                    println!("  No insulin delivery records found.");
                                }
                            }
                        }
                        
                        println!("\nRecent Glucose Readings:");
                        let glucose_query = "
                            SELECT glucose_level, reading_time, status
                            FROM glucose_readings
                            WHERE patient_id = CAST(?1 AS INTEGER)
                            ORDER BY reading_time DESC
                            LIMIT 5
                        ";
                        
                        if let Ok(mut gstmt) = conn.prepare(glucose_query) {
                            if let Ok(readings) = gstmt.query_map([&pid], |row| {
                                Ok((
                                    row.get::<_, f64>(0)?,
                                    row.get::<_, String>(1)?,
                                    row.get::<_, String>(2)?,
                                ))
                            }) {
                                let mut count = 0;
                                for reading in readings {
                                    if let Ok((level, time, status)) = reading {
                                        println!("  {:.1} mg/dL ({}) at {}", level, status, time);
                                        count += 1;
                                    }
                                }
                                if count == 0 {
                                    println!("  No glucose readings found.");
                                }
                            }
                        }
                    }
                },
                Err(e) => println!("Error fetching patients: {}", e),
            }
        },
        Err(e) => println!("Error preparing query: {}", e),
    }
}

