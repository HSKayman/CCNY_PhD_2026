use rusqlite::Connection;

pub struct InsulinLog {
	pub dosage_id: i64,
	pub patient_id: String,
	pub action_type: String,
	pub dosage_units: f64,
	pub requested_by: String,
	pub dosage_time: String,
}

pub struct GlucoseReading {
	pub reading_id: i64,
	pub patient_id: String,
	pub glucose_level: f64,
	pub reading_time: String,
	pub status: String,
}

pub fn get_glucose_reading(conn: &Connection, patient_id: &str) -> rusqlite::Result<(Vec<InsulinLog>, Vec<GlucoseReading>)> {
	// === Fetch insulin logs ===
	let mut insulin_stmt = conn.prepare(
		"SELECT dosage_id, patient_id, action_type, dosage_units, requested_by, dosage_time
		 FROM insulin_logs
		 WHERE patient_id = ?1"
	)?;

	let insulin_iter = insulin_stmt.query_map(rusqlite::params![patient_id], |row| {
		Ok(InsulinLog {
			dosage_id: row.get(0)?,
			patient_id: row.get(1)?,
			action_type: row.get(2)?,
			dosage_units: row.get(3)?,
			requested_by: row.get(4)?,
			dosage_time: row.get(5)?,
		})
	})?;

	let insulin_logs: Vec<InsulinLog> = insulin_iter.filter_map(|r| r.ok()).collect();

	
	let mut glucose_stmt = conn.prepare(
		"SELECT reading_id, patient_id, glucose_level, reading_time, status
		 FROM glucose_readings
		 WHERE patient_id = ?1"
	)?;

	let glucose_iter = glucose_stmt.query_map(rusqlite::params![patient_id], |row| {
		Ok(GlucoseReading {
			reading_id: row.get(0)?,
			patient_id: row.get(1)?,
			glucose_level: row.get(2)?,
			reading_time: row.get(3)?,
			status: row.get(4)?,
		})
	})?;

	let glucose_logs: Vec<GlucoseReading> = glucose_iter.filter_map(|r| r.ok()).collect();

	// Return both in a tuple
	Ok((insulin_logs, glucose_logs))
}

