#!/usr/bin/env python3
import csv
import sqlite3
from pathlib import Path

DB_PATH = Path("data/database.db")
CSV_PATH = Path("pump_simm/gcm_reader.csv")

def main():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.execute("PRAGMA foreign_keys = ON;")
        cur = conn.cursor()

        # Recreate temp table with explicit column names
        cur.execute("DROP TABLE IF EXISTS temp_insulin_pump;")
        cur.execute("""
            CREATE TABLE temp_insulin_pump (
              patient_id TEXT,
              action_type TEXT,
              dosage_units INT,
              requested_by TEXT
            );
        """)

        # Load CSV (skip header)
        with CSV_PATH.open(newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)  # skip header row if present
            rows = []
            for row in reader:
                if not row or len(row) < 3:
                    continue
                patient_id = row[0]
                action_type = row[1]
                dosage_units = row[2]
                requested_by = row[3] if len(row) >= 4 and row[3] else "device"
                rows.append((patient_id, action_type, dosage_units, requested_by))

        if rows:
            cur.executemany(
                "INSERT INTO temp_insulin_pump (patient_id, action_type, dosage_units, requested_by) VALUES (?, ?, ?, ?);",
                rows,
            )

        # Insert into final table, forcing current timestamp in dosage_time
        cur.execute("""
            INSERT INTO insulin_logs (patient_id, action_type, dosage_units, requested_by, dosage_time)
            SELECT patient_id, action_type, dosage_units, requested_by, datetime('now')
            FROM temp_insulin_pump;
        """)

        cur.execute("DROP TABLE temp_insulin_pump;")
        conn.commit()
        print("Imported insulin logs successfully.")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
