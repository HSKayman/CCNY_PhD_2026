// core data models for database interaction

#[derive(Debug)]
pub struct User{
    pub id: String,
    pub user_name: String,
    pub password_hash: String,
    pub role: String,
    pub created_at: String,
    pub last_login: Option<String>
}
#[derive(Debug)]
pub struct Patient{
    pub patient_id: String,
    pub first_name: String,
    pub last_name: String,
    pub date_of_birth: String,
    pub basal_rate: f32,
    pub bolus_rate: f32,
    pub max_dosage: f32,
    pub low_glucose_threshold: f32,
    pub high_glucose_threshold: f32,
    pub clinician_id: String,
    pub caretaker_id: String
}
#[derive(Debug)]
pub struct PatientCareTeam{
    care_taker_id: i32,
    patient_id_list: Vec<i32>
}
#[derive(Debug)]
pub struct GlucoseReading{
    reading_id: i32,
    patient_id: i32,
    glucose_level: f32,
    reading_time: String,
    status: String
}
#[derive(Debug)]
pub struct InsulinLog{
    dosage_id: i32,
    patient_id: i32,
    action_type: String,
    dosage_units: f32,
    requested_by: String,
    dosage_time: String
}
#[derive(Debug)]
pub struct Alerts{
    alert_id: i32,
    patient_id: i32,
    alert_type: String,
    alert_message: String,
    alert_time: String,
    is_resolved: bool,
    resolved_by: Option<String>,
}
#[derive(Debug)]
pub struct MealLog{
    meal_id: i32,
    patient_id: i32,
    carbohydrate_amount: f32,
    meal_time: String
}
#[derive(Debug)]
pub struct Session{
    session_id: i32,
    username: String,
    creation_time: String,
    expiration_time: Option<String>,
    active: bool,
}
