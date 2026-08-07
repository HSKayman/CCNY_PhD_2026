# CCNY_PhD_2026

Coursework and lab projects from City College of New York (CCNY) PhD / graduate studies, organized by course area.

## Computer Vision

CSc I6716 materials: early homework (MATLAB/images under `HW1`–`HW3`), stereo vision (`HW4` — fundamental matrix, epipoles, epipolar matching in Python/notebook), and a final project that removes window-screen artifacts from video via motion compensation and temporal filtering (`Project/`).

## Secure Cloud Computing

`Ropetyapp-devsec-main/` — RoboPety, a Flask + Cloud SQL “robot pet” web app hardened for a secure-cloud course: JWT/bcrypt auth, 2FA (TOTP), reCAPTCHA, password policy, Secret Manager, rate limiting, Talisman, GCS uploads, admin/blue-team workflows, and SQL/App Engine deploy scripts.

## Secure Systems Engineering

Rust- and systems-security labs, including:

- **aid_adv / GlucoGuard** — automated insulin delivery (AID) simulation; Python pump helpers import CGM / insulin CSV data into SQLite.
- **e_voting_system** — role-based electronic voting (Rust), plus a script to cross-build “ghost” debug binaries.
- **lab-crypto-engineering** — cryptographic engineering lab (image encrypt/decrypt workflow).
- **slot-machine-main** — casino/slot-machine CLI with auth, crypto RNG, and SQLite logging.
- **guessing_game**, **minigrep**, **trojan-horse** — smaller Rust exercises from the same course track.
