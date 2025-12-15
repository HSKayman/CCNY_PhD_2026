# 🩺 GlucoGuard Systems — Automated Insulin Delivery (AID) 

📘 Project Description

GlucoGuard Systems is an open-source Automated Insulin Delivery (AID) System simulation written in Rust.
The project aims to model real-world insulin pump behavior by:

- Simulating continuous glucose monitoring (CGM) readings.

- Delivering safe, automated basal and bolus insulin doses.

- Generating alerts for high or low glucose levels.

- Providing secure access and role-based control for admins, clinicians, caretakers, auditors, and patients.

- This system supports CLI interaction and can later be extended with a web or GUI interface for visualization and management.

⚙️ Features

- Continuous glucose simulation with configurable input.

- Safe insulin dose calculation with built-in limits.

- Role-based authentication (Admin, Auditor, Clinician, Caretaker, Patient).

- Real-time alerts and secure logging of all operations.

- Extendable for web or GUI front-end visualization.

🧩 Project Structure
```
glucoguard/
├── build.rs                 # Import glucose simulation data from reader to database in compiler time
├── logs/                    # Event log
├── pump_simm/               # Simulated patient-reader output
├── src/
│   ├── main.rs              # Entry point (CLI handling)
│   ├── cgm.rs               # CGM data simulation and parsing
│   ├── insulin.rs           # Basal/Bolus insulin control logic
│   ├── auth.rs              # Authentication and role management
│   ├── user.rs              # User and Role Data Structures
│   ├── alerts.rs            # Alert generation for glucose 
│   ├── logger.rs            # Logging and data persistence
│   ├── access_control.rs    # Access management
│   ├── input_validation.rs  # Input validation helper functions
│   ├── diagnostic.rs        # System diagnostic
│   ├── db/                  # Database set up and connection handling
│   ├── menus/               # Role-base user menus
│   └── utils.rs             # Helper functions
├── data/
│   └── database.db          # Database
├── Cargo.toml               # Rust project configuration
└── README.md

```
🧰 Setup Instructions
- Build the Project
```
cargo build
```
- Run the Project
```
cargo run
```


You can also feed glucose readings via STDIN or socket input.

👥 Contributing

Fork the repository and create your own branch:

```
git checkout -b feature/your-feature-name
```


Commit your changes with clear messages:

```
git commit -m "Add CGM simulation logic"
```


Push your branch and create a pull request:

```
git push origin feature/your-feature-name
```


Wait for team review before merging into main.

🧪 Testing

Run tests with:

```
cargo test

```


Add tests for new modules or edge cases (invalid data, overdose prevention, etc.).

🔒 Security & Safety

All critical actions (doses, alerts, settings) must be logged with timestamps and user roles.

Follow secure coding practices and handle user authentication carefully.

Never push real patient data or credentials to the repository.

🧑‍💻 Team: GlucoGuard Systems

[Anwar Jahid] 

[Kwame Davour] 

[MD Younus] 

[Honore Mandiamy] 

🧑‍💻 Team: ThermoRust (ADVERSARY)
[Proma Roy]

[Md Ariful Islam Fahim]

[Hsiao-Yin Peng]

[Tahsinur Rahman]
