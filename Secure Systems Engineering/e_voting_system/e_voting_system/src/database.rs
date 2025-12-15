use rusqlite::{params, Connection, Result, OptionalExtension}; // Here we import rusqlite for SQLite database handling


pub struct Database {
    conn: Connection,
}


impl Database {
    pub fn new(db_path: &str) -> Result<Self> {
        let conn = Connection::open(db_path)?;
        let db = Database { conn };
        db.initialize_tables()?; // will create/update tables
        Ok(db)
    }

/// Initializes all necessary tables for the e-voting system and make sure it won't overwrite existing data
    fn initialize_tables(&self) -> Result<()> {
        self.conn.execute_batch(
            "
            CREATE TABLE IF NOT EXISTS elections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'closed'
            );
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                FOREIGN KEY(election_id) REFERENCES elections(id)
            );
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                position_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                party TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(position_id) REFERENCES positions(id)
            );
            CREATE TABLE IF NOT EXISTS voters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS votes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                election_id INTEGER NOT NULL,
                position_id INTEGER NOT NULL,
                candidate_id INTEGER NOT NULL,
                voter_id INTEGER NOT NULL,
                FOREIGN KEY(election_id) REFERENCES elections(id),
                FOREIGN KEY(position_id) REFERENCES positions(id),
                FOREIGN KEY(candidate_id) REFERENCES candidates(id),
                FOREIGN KEY(voter_id) REFERENCES voters(id)
            );
            "
        )?;
        crate::audit::setup_audit_table(&self.conn);
        Ok(())
    }


    // ------------------- ADMIN METHODS -------------------


    pub fn create_election(&self, name: &str) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO elections (name) VALUES (?1)",
            params![name],
        )?;
        Ok(self.conn.last_insert_rowid())
    }


    pub fn add_position(&self, election_id: i64, name: &str) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO positions (election_id, name) VALUES (?1, ?2)",
            params![election_id, name],
        )?;
        Ok(self.conn.last_insert_rowid())
    }


    /// Add candidate along with party
    pub fn add_candidate_with_party(&self, position_id: i64, name: &str, party: &str) -> Result<i64> {
        self.conn.execute(
            "INSERT INTO candidates (position_id, name, party) VALUES (?1, ?2, ?3)",
            params![position_id, name, party],
        )?;
        Ok(self.conn.last_insert_rowid())
    }


    /// Register a new voter
pub fn register_voter(&self, full_name: &str, date_of_birth: &str) -> Result<bool> {
    // Check if voter already exists
    let mut stmt = self.conn.prepare(
        "SELECT id FROM voters WHERE full_name = ?1 AND date_of_birth = ?2"
    )?;
    let exists: Option<i64> = stmt.query_row(params![full_name, date_of_birth], |row| row.get(0)).optional()?;


    if exists.is_some() {
        return Ok(false); // already exists
    }


    // Insert new voter
    self.conn.execute(
        "INSERT INTO voters (full_name, date_of_birth) VALUES (?1, ?2)",
        params![full_name, date_of_birth],
    )?;


    Ok(true)
}




    // ------------------- ELECTION METHODS -------------------


    pub fn list_elections(&self) -> Result<Vec<(i64, String, String)>> {
        let mut stmt = self.conn.prepare("SELECT id, name, status FROM elections")?;
        let rows = stmt.query_map([], |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)))?;
        let mut elections = Vec::new();
        for e in rows {
            elections.push(e?);
        }
        Ok(elections)
    }


    pub fn open_election(&self, election_id: i64) -> Result<()> {
        self.conn.execute(
            "UPDATE elections SET status = 'open' WHERE id = ?1",
            params![election_id],
        )?;
        Ok(())
    }


    pub fn close_election(&self, election_id: i64) -> Result<()> {
        self.conn.execute(
            "UPDATE elections SET status = 'closed' WHERE id = ?1",
            params![election_id],
        )?;
        Ok(())
    }


    pub fn get_election_status(&self, election_id: i64) -> Result<String> {
        self.conn.query_row(
            "SELECT status FROM elections WHERE id = ?1",
            params![election_id],
            |row| row.get(0),
        )
    }


    pub fn tally_results(&self, election_id: i64) -> Result<Vec<(String, String, i64)>> {
        let mut stmt = self.conn.prepare(
            "
            SELECT positions.name, candidates.name, COUNT(votes.id) as vote_count
            FROM positions
            JOIN candidates ON candidates.position_id = positions.id
            LEFT JOIN votes ON votes.candidate_id = candidates.id AND votes.election_id = ?1
            WHERE positions.election_id = ?1
            GROUP BY positions.name, candidates.name
            "
        )?;
        let rows = stmt.query_map(params![election_id], |row| {
            Ok((row.get(0)?, row.get(1)?, row.get(2)?))
        })?;
        let mut results = Vec::new();
        for r in rows {
            results.push(r?);
        }
        Ok(results)
    }


    // ------------------- VOTER METHODS -------------------


    pub fn list_positions(&self, election_id: i64) -> Result<Vec<(i64, String)>> {
        let mut stmt = self.conn.prepare(
            "SELECT id, name FROM positions WHERE election_id = ?1"
        )?;
        let rows = stmt.query_map(params![election_id], |row| Ok((row.get(0)?, row.get(1)?)))?;
        let mut positions = Vec::new();
        for r in rows {
            positions.push(r?);
        }
        Ok(positions)
    }


    pub fn list_candidates(&self, position_id: i64) -> Result<Vec<(i64, String, String)>> {
    let mut stmt = self.conn.prepare(
        "SELECT id, name, party FROM candidates WHERE position_id = ?1"
    )?;
    let rows = stmt.query_map(params![position_id], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?))
    })?;
    let mut candidates = Vec::new();
    for r in rows {
        candidates.push(r?);
    }
    Ok(candidates)
}




    pub fn cast_vote(&self, election_id: i64, position_id: i64, candidate_id: i64, voter_id: i64) -> Result<()> {
        self.conn.execute(
            "INSERT INTO votes (election_id, position_id, candidate_id, voter_id) VALUES (?1, ?2, ?3, ?4)",
            params![election_id, position_id, candidate_id, voter_id],
        )?;
        Ok(())
    }


    pub fn has_voted(&self, election_id: i64, position_id: i64, voter_id: i64) -> Result<bool> {
        let mut stmt = self.conn.prepare(
            "SELECT id FROM votes WHERE election_id = ?1 AND position_id = ?2 AND voter_id = ?3"
        )?;
        let exists: Option<i64> = stmt.query_row(params![election_id, position_id, voter_id], |row| row.get(0)).optional()?;
        Ok(exists.is_some())
    }


    pub fn list_open_elections(&self) -> Result<Vec<(i64, String)>> {
        let mut stmt = self.conn.prepare("SELECT id, name FROM elections WHERE status = 'open'")?;
        let rows = stmt.query_map([], |row| Ok((row.get(0)?, row.get(1)?)))?;
        let mut elections = Vec::new();
        for r in rows {
            elections.push(r?);
        }
        Ok(elections)
    }


    pub fn get_voter_id(&self, full_name: &str, dob: &str) -> Result<Option<i64>> {
        let mut stmt = self.conn.prepare(
            "SELECT id FROM voters WHERE full_name = ?1 AND date_of_birth = ?2"
        )?;
        let result: Option<i64> = stmt.query_row(params![full_name, dob], |row| row.get(0)).optional()?;
        Ok(result)
    }


    pub fn get_votes_by_voter(&self, voter_id: i64) -> Result<Vec<(String, String, String, String)>> {
    let mut stmt = self.conn.prepare(
        "
        SELECT e.name, p.name, c.name, c.party
        FROM votes v
        JOIN elections e ON e.id = v.election_id
        JOIN positions p ON p.id = v.position_id
        JOIN candidates c ON c.id = v.candidate_id
        WHERE v.voter_id = ?1
        "
    )?;
    let rows = stmt.query_map([voter_id], |row| {
        Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?))
    })?;
    let mut results = Vec::new();
    for r in rows {
        results.push(r?);
    }
    Ok(results)
    }

    pub fn get_voter_name(&self, voter_id: i64) -> Result<Option<String>> {
        let mut stmt = self.conn.prepare("SELECT full_name FROM voters WHERE id = ?1")?;
        let result: Option<String> = stmt.query_row(params![voter_id], |row| row.get(0)).optional()?;
        Ok(result)
    }

    pub fn connection(&self) -> &Connection {
        &self.conn
    }

}