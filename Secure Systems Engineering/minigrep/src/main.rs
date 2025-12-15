// 1. Describe the process of reading and iterating over file contents in Rust. How is this different
// from other languages you might be familiar with?
// Answer: 
// First of all, we're defining a string vector variable called "args", 
// also, "config" variable which has Config data structure.
// We implemented custom built in function, which called 'build'. 
// In this function we're checking number of arguments to ensure user enter correct number of input. 
// This function returns the keywords, file_name and also user can control case sensitive or insensitive securely.
// If error persists: such as number of argument error, file name error or any other errors the program ends securely with error message.
// The run function was implemented securely and task of this function is checking the ignore case to call correct search function.
// If user wants ignore_case this function will call regular search function in lib.rs. If not this function will call insensitive search function.
// The search function accepts two parameters which are keyword and file_content.
// This search function is checking the keyword line by line if the line contains the keyword and append the whole line in the result vector. 
// To print each in terminal or write it in output file that user defined. 
// rust looks like more secure and efficent than other languages because of ownership mechanism.

// 2. Explain the benefits of using external libraries for the tasks in this project. Would you have
// implemented this functionality yourself, or was it better to use an existing library?
// Answer: The existing libraries makes it easier for us to test our cases. This helps us to reduce bug.

// 3. Explain the drawbacks of using external libraries for the tasks in this project. Try to think like
// a security engineer – what could go wrong?
// Answer: We used pub to make the functions public. It may be vulnerable to the external threats. And it requires more effort for the developers to implement external libraries.

// 4. Discuss the challenges you faced while implementing the minigrep functionality. How did
// you overcome them?
// Answer: We struggled to get used to ownership mechanism in Rust. And we didn't understand the proper function of "&" and ";", 
// they're not like in C. We're not familiar with writing test cases.

// 5. Reflect on the importance of code testing and documentation in a project
// like minigrep . How did you test your code? Why was it helpful?
// Answer: We wrote our test cases in the lib.rs file. It was very easy to run test cases. 
// We haven't noticed this feature in other languages before. It would enough running tests by typing 'cargo test' only.

// 6. Describe any specific skills or tools you learned or used that you can apply to future
// projects
// Answer: 1. raising error in other functions and handling erron in main function.
// 2. Test cases.
// 3. Lifetime signature: the variable that needs to be stored for future operations, can be stored using this feature.
//  we understand that it tells the compiler how long returned references will live/be stored
//  by connecting them to lifetime of input data they borrow from.

// Noted: We answered these question by discussing together. 

use std::env;
use std::error::Error;
use std::fs;
use std::process;

use minigrep::{search, search_case_insensitive};

fn main() {
    let args: Vec<String> = env::args().collect();

    let config = Config::build(&args).unwrap_or_else(|err| {
        eprintln!("Problem parsing arguments: {err}");
        process::exit(1);
    });

    if let Err(e) = run(config) {
        eprintln!("Application error: {e}");
        process::exit(1);
    }
}

pub struct Config {
    pub query: String,
    pub file_path: String,
    pub ignore_case: bool,
}

impl Config {
    fn build(args: &[String]) -> Result<Config, &'static str> {
        if args.len() < 3 {
            return Err("not enough arguments");
        }

        let query = args[1].clone();
        let file_path = args[2].clone();

        let ignore_case = env::var("IGNORE_CASE").is_ok();

        Ok(Config {
            query,
            file_path,
            ignore_case,
        })
    }
}

fn run(config: Config) -> Result<(), Box<dyn Error>> {
    let contents = fs::read_to_string(config.file_path)?;

    let results = if config.ignore_case {
        search_case_insensitive(&config.query, &contents)
    } else {
        search(&config.query, &contents)
    };

    for line in results {
        println!("{line}");
    }

    Ok(())
}