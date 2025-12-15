use std::process::{Command, Stdio};
use std::fs;

const LOG_PATH: &str = "pump_simm/python_build.log"; // log file path

fn import_data(script: &str, log: &mut String, clean: bool) {
    use std::fmt::Write as _;

    // Determine the python command based on the platform
    #[cfg(target_os = "windows")]
    let python_cmd = "python";
    #[cfg(not(target_os = "windows"))]
    let python_cmd = "python3";

    #[cfg(target_os = "windows")]
    use std::os::windows::process::CommandExt;
    #[cfg(target_os = "windows")]
    const CREATE_NO_WINDOW: u32 = 0x08000000;

    // Build command (platform-specific)
    let mut cmd = Command::new(python_cmd);
    cmd.arg(script)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());

    #[cfg(target_os = "windows")]
    cmd.creation_flags(CREATE_NO_WINDOW);

    let output = cmd
        .output()
        .expect("Failed to start python process");

    if clean {
        std::thread::sleep(std::time::Duration::from_secs(1));
        fs::remove_file(script).ok();
    }

    // Write results to log string
    writeln!(log, "==== Running {script} ====").unwrap();
    writeln!(log, "status: {:?}\n", output.status).unwrap();
    writeln!(log, "--- STDOUT ---").unwrap();
    writeln!(log, "{}", String::from_utf8_lossy(&output.stdout)).unwrap();
    writeln!(log, "--- STDERR ---").unwrap();
    writeln!(log, "{}", String::from_utf8_lossy(&output.stderr)).unwrap();
    writeln!(log, "\n==============================\n").unwrap();

}

fn main() {
    let mut log = String::new();

    // import reader data to database(glucose/insulin/pump)
    import_data("pump_simm/gcm_reader.py", &mut log, false);
    import_data("pump_simm/glucose.py", &mut log, true);
    import_data("pump_simm/insulin_pump.py", &mut log, false);

    // write log to file
    fs::write(LOG_PATH, log).expect("Failed to write python_build.log");
}
