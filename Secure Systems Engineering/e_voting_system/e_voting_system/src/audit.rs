use rusqlite::{params, Connection};
use chrono::Local;

// Function to create the audit_log table if it doesn't already exist
pub fn setup_audit_table(conn: &Connection) {
    conn.execute(
        "CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            voter_name TEXT,
            candidate_name TEXT,
            action TEXT,
            timestamp TEXT
        )",
        [], // No parameters needed for table creation
    ).unwrap();
}

// Function to log a vote into the audit_log table
pub fn log_vote(conn: &Connection, voter: &str, candidate: &str) {
    // Get current timestamp in "YYYY-MM-DD HH:MM:SS" format
    let ts = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

    // Insert a new record into audit_log
    conn.execute(
        "INSERT INTO audit_log (voter_name, candidate_name, action, timestamp)
         VALUES (?1, ?2, 'vote_cast', ?3)",
        params![voter, candidate, ts], // Bind parameters to prevent SQL injection
    ).unwrap();
}

// Function to display all records from audit_log
pub fn show_audit_log(conn: &Connection) {
    // Prepare a SELECT statement to fetch all audit logs in descending order
    let mut stmt = conn.prepare(
        "SELECT voter_name, candidate_name, action, timestamp FROM audit_log ORDER BY id DESC"
    ).unwrap();

    // Execute the query and map each row to a tuple
    let rows = stmt.query_map([], |r| {
        Ok((
            r.get::<_, String>(0)?, 
            r.get::<_, String>(1)?, 
            r.get::<_, String>(2)?, 
            r.get::<_, String>(3)?
        ))
    }).unwrap();

    println!("\n=== Audit Log ===");

    // Iterate over the results and print them
    for row in rows {
        let (voter, cand, action, ts) = row.unwrap();
        println!("{ts}: {voter} -> {cand} [{action}]");
    }
}