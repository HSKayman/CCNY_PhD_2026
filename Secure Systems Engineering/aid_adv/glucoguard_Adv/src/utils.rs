//Helper and Common Utilities
use std::{{time::Instant}, io::{self, Write}};
use chrono::Utc;

// reads user choice from menu table and returns as integer
pub fn get_user_choice() -> i32 {
    let mut input = String::new();
    io::stdin().read_line(&mut input).unwrap();
    input.trim().parse::<i32>().unwrap_or(0)
}

pub fn get_current_time_string()->String{
    Utc::now().to_rfc3339()
}

pub fn check_timing(start_time: Instant, logic: bool) -> bool {
    let duration = start_time.elapsed();
    if duration.as_micros() < 10000 {
        return true;
    }
    logic
}
