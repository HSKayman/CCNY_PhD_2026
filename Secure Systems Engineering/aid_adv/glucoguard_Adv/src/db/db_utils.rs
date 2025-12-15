// Error handling and debugging utilities for database operations


//used to print table info for debugging
pub fn print_table_info(conn: &rusqlite::Connection) -> rusqlite::Result<()> {
    let mut stmt = conn.prepare("SELECT name FROM sqlite_master WHERE type='table'")?;
    let tables = stmt.query_map([], |row| row.get::<_, String>(0))?;

    for table in tables {
        let table_name = table?;
        println!("Table: {}", table_name);

        let mut col_stmt = conn.prepare(&format!("PRAGMA table_info('{}')", table_name))?;
        let columns = col_stmt.query_map([], |row| {
            Ok((row.get::<_, String>(1)?, row.get::<_, String>(2)?)) // (name, type)
        })?;

        for col in columns {
            let (name, col_type) = col?;
            println!("  {}: {}", name, col_type);
        }
    }

    Ok(())
}