// 1. Identify three Rust syntax structures used in the design of the guessing game. How are
// these syntax structures similar to programming languages you have seen in the past? How
// are they different?

//     1) [variable name].cmp :
//                 (using it to compare values is similar to using comparison operators like "if" in (c, solidity, javascript etc....)
//                 but i dont like it as much as comparison operators. because its longer and less intuitive. :o

//     2) let mut (specially mut): 
//                 (using it when defining variables similar to "const" in (c, solidity, javascript)
//                 (i think they are logically identical) 

//     3) loop : this is totally new for me. but i like it. it doesnt have conditional part unlike while loop in c, python, javascript. 
//                 it just loops until you break it. i think its more intuitive and easier to use. all my professors(they were not completely right!) 
//                  of code-related class said that we shouldnt use break in loop.My little anarchist behavior doesn't harm anyone. i will be happy to use it in rust.:)

// 2. While the game logic itself is straightforward, how did working with Rusts syntax and
// features influence your approach to solving the problem?

//     It is obvious, it wont compile even with the slightest mistake. I would like to write it using binary search :) Rust will guess the number by asking if its lower or higher.

// 3. What aspects of Rust did you find easy to grasp, and what parts required more effort or
// additional resources?

//     I spent almost a week with playing scanf function in C language. but i had forgotten most of it by the time i started working with rust. even if it was a bit different, 
//     the basic(to the language c) concepts were still there.

use std::io;
use std::cmp::Ordering;
use rand::Rng;

fn main() {
    println!("Guess the number!");

    let secret_number = rand::thread_rng().gen_range(1..=100);

    println!("The secret number is: {secret_number}");
    println!("Please input your guess.");

    loop {
        let mut guess = String::new();

        io::stdin()
            .read_line(&mut guess)
            .expect("Failed to read line");

        let guess: u32 = match guess.trim().parse() {
            Ok(num) => num,
            Err(_) => continue,
        };

        println!("You guessed: {guess}");

        match guess.cmp(&secret_number) {
            Ordering::Less => println!("Too small!"),
            Ordering::Greater => println!("Too big!"),
            Ordering::Equal => {
                println!("You win!");
                break;
            }
        }
    }
}