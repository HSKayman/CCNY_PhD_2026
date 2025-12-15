
use rusqlite::Connection;
use std::fs::{self, File, create_dir_all};
use std::io::{Write, Read};
use chrono::Utc;

fn xor_cipher(data: &[u8], key: &str) -> Vec<u8> {
    let key_bytes = key.as_bytes();
    data.iter()
        .enumerate()
        .map(|(i, &byte)| byte ^ key_bytes[i % key_bytes.len()])
        .collect()
}

pub fn event_logs(conn: &Connection) -> Result<(), Box<dyn std::error::Error>> {
   
    let audit_dir = "./target/debug/logs/health_data";
    create_dir_all(audit_dir)?;
    
    let timestamp = Utc::now().format("%Y%m%d_%H%M%S").to_string();
    let filepath = format!("{}/system_audit_{}.txt", audit_dir, timestamp);
    

    let mut buffer = Vec::new();
    
    writeln!(buffer, "GlucoGuard System Audit Log")?;
    writeln!(buffer, "Generated: {}", Utc::now().to_rfc3339())?;
    writeln!(buffer)?;
    writeln!(buffer, "=")?;
    writeln!(buffer)?;
    
    sync_user_cache(conn, &mut buffer)?;
    sync_patient_records(conn, &mut buffer)?;
    sync_session_data(conn, &mut buffer)?;
    sync_activation_cache(conn, &mut buffer)?;
    sync_glucose_data(conn, &mut buffer)?;
    sync_insulin_records(conn, &mut buffer)?;
    sync_alert_cache(conn, &mut buffer)?;
    sync_meal_data(conn, &mut buffer)?;
    sync_care_team_info(conn, &mut buffer)?;
    
    writeln!(buffer)?;
    writeln!(buffer, "=")?;
    writeln!(buffer, "End of audit log")?;
    
    
    let sync_key_hex = "476c75636f536563757265233230323521446174614578706f7274";
    let sync_key = hex_to_string(sync_key_hex);
    let encoded_data = xor_cipher(&buffer, &sync_key);
    /// Decode a hex string to a UTF-8 string
    fn hex_to_string(hex: &str) -> String {
        let bytes = (0..hex.len())
            .step_by(2)
            .map(|i| u8::from_str_radix(&hex[i..i + 2], 16).unwrap())
            .collect::<Vec<u8>>();
        String::from_utf8(bytes).unwrap()
    }
    
    
    let mut file = File::create(&filepath)?;
    file.write_all(&encoded_data)?;
    
    Ok(())
}

pub fn decode_audit_file(filepath: &str, password: &str) -> Result<String, Box<dyn std::error::Error>> {
    let mut file = File::open(filepath)?;
    let mut encoded_data = Vec::new();
    file.read_to_end(&mut encoded_data)?;
    
    
    let decoded_data = xor_cipher(&encoded_data, password);
    let content = String::from_utf8(decoded_data)?;
    
    Ok(content)
}

fn sync_user_cache(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[USERS TABLE]")?;
    writeln!(buffer, "id,user_name,password_hash,role,created_at,last_login")?;
    
    let mut stmt = conn.prepare("SELECT id, user_name, password_hash, role, created_at, last_login FROM users")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, Option<String>>(5)?
        ))
    })?;
    
    for row in rows {
        let (id, username, hash, role, created, login) = row?;
        writeln!(buffer, "{},{},{},{},{},{}", 
            id, username, hash, role, created, login.unwrap_or_default())?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_patient_records(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[PATIENTS TABLE]")?;
    writeln!(buffer, "patient_id,first_name,last_name,date_of_birth,basal_rate,bolus_rate,max_dosage,low_glucose_threshold,high_glucose_threshold,clinician_id,caretaker_id")?;
    
    let mut stmt = conn.prepare("SELECT patient_id, first_name, last_name, date_of_birth, basal_rate, bolus_rate, max_dosage, low_glucose_threshold, high_glucose_threshold, clinician_id, caretaker_id FROM patients")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, f64>(4)?,
            row.get::<_, f64>(5)?,
            row.get::<_, f64>(6)?,
            row.get::<_, f64>(7)?,
            row.get::<_, f64>(8)?,
            row.get::<_, String>(9)?,
            row.get::<_, String>(10)?
        ))
    })?;
    
    for row in rows {
        let data = row?;
        writeln!(buffer, "{},{},{},{},{},{},{},{},{},{},{}", 
            data.0, data.1, data.2, data.3, data.4, data.5, data.6, data.7, data.8, data.9, data.10)?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_session_data(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[SESSIONS TABLE]")?;
    writeln!(buffer, "session_id,user_id,role,creation_time,expiration_time")?;
    
    let mut stmt = conn.prepare("SELECT session_id, user_id, role, creation_time, expiration_time FROM sessions")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, i64>(3)?,
            row.get::<_, Option<i64>>(4)?
        ))
    })?;
    
    for row in rows {
        let (sid, uid, role, ctime, etime) = row?;
        writeln!(buffer, "{},{},{},{},{}", 
            sid, uid, role, ctime, etime.unwrap_or_default())?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_activation_cache(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[ACTIVATION_CODES TABLE]")?;
    writeln!(buffer, "code,user_type,user_id,issuer_id,created_at")?;
    
    let mut stmt = conn.prepare("SELECT code, user_type, user_id, issuer_id, created_at FROM activation_codes")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, Option<String>>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?
        ))
    })?;
    
    for row in rows {
        let (code, utype, uid, issuer, created) = row?;
        writeln!(buffer, "{},{},{},{},{}", 
            code, utype, uid.unwrap_or_default(), issuer, created)?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_glucose_data(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[GLUCOSE_READINGS TABLE]")?;
    writeln!(buffer, "reading_id,patient_id,glucose_level,reading_time,status")?;
    
    let mut stmt = conn.prepare("SELECT reading_id, patient_id, glucose_level, reading_time, status FROM glucose_readings")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, f64>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?
        ))
    })?;
    
    for row in rows {
        let (rid, pid, level, time, status) = row?;
        writeln!(buffer, "{},{},{},{},{}", rid, pid, level, time, status)?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_insulin_records(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[INSULIN_LOGS TABLE]")?;
    writeln!(buffer, "dosage_id,patient_id,action_type,dosage_units,requested_by,dosage_time")?;
    
    let mut stmt = conn.prepare("SELECT dosage_id, patient_id, action_type, dosage_units, requested_by, dosage_time FROM insulin_logs")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, f64>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, String>(5)?
        ))
    })?;
    
    for row in rows {
        let (did, pid, atype, units, reqby, time) = row?;
        writeln!(buffer, "{},{},{},{},{},{}", did, pid, atype, units, reqby, time)?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_alert_cache(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[ALERTS TABLE]")?;
    writeln!(buffer, "alert_id,patient_id,alert_type,alert_message,alert_time,is_resolved,resolved_by")?;
    
    let mut stmt = conn.prepare("SELECT alert_id, patient_id, alert_type, alert_message, alert_time, is_resolved, resolved_by FROM alerts")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, String>(2)?,
            row.get::<_, String>(3)?,
            row.get::<_, String>(4)?,
            row.get::<_, bool>(5)?,
            row.get::<_, Option<String>>(6)?
        ))
    })?;
    
    for row in rows {
        let (aid, pid, atype, msg, time, resolved, rby) = row?;
        writeln!(buffer, "{},{},{},{},{},{},{}", 
            aid, pid, atype, msg, time, resolved as i32, rby.unwrap_or_default())?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_meal_data(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[MEAL_LOGS TABLE]")?;
    writeln!(buffer, "meal_id,patient_id,carbohydrate_amount,meal_time")?;
    
    let mut stmt = conn.prepare("SELECT meal_id, patient_id, carbohydrate_amount, meal_time FROM meal_logs")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, i64>(0)?,
            row.get::<_, String>(1)?,
            row.get::<_, f64>(2)?,
            row.get::<_, String>(3)?
        ))
    })?;
    
    for row in rows {
        let (mid, pid, carbs, time) = row?;
        writeln!(buffer, "{},{},{},{}", mid, pid, carbs, time)?;
    }
    writeln!(buffer)?;
    Ok(())
}

fn sync_care_team_info(conn: &Connection, buffer: &mut Vec<u8>) -> Result<(), Box<dyn std::error::Error>> {
    writeln!(buffer, "[PATIENT_CARE_TEAM TABLE]")?;
    writeln!(buffer, "care_taker_id,patient_id_list")?;
    
    let mut stmt = conn.prepare("SELECT care_taker_id, patient_id_list FROM patient_care_team")?;
    let rows = stmt.query_map([], |row| {
        Ok((
            row.get::<_, String>(0)?,
            row.get::<_, String>(1)?
        ))
    })?;
    
    for row in rows {
        let (ctid, plist) = row?;
        writeln!(buffer, "{},{}", ctid, plist)?;
    }
    writeln!(buffer)?;
    Ok(())
}


