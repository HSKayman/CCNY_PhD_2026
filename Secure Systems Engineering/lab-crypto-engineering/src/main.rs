use std::fs;

use aes_gcm::{
    aead::{Aead, OsRng},
    AeadCore, Aes256Gcm, Key, KeyInit,
};
use base64::prelude::*;
use sha2::{Digest, Sha256};
use x25519_dalek::{PublicKey, StaticSecret};

/// Save bytes to file encoded as Base64.
///
/// The data is encoded using the standard Base64 encoding engine and written to
/// disk.
///
/// # Arguments
///
/// * `file_name` - the path of the file in which the data is to be saved
/// * `data` - the data of to be saved to file
///
/// # Note
///
/// You may **not** change the signature of this function.
///
fn save_to_file_as_b64(file_name: &str, data: &[u8]) {
    let encoded=BASE64_STANDARD.encode(data);
    fs::write(file_name, encoded).unwrap();
}

/// Read a Base64-encoded file as bytes.
///
/// The data is read from disk and decoded using the standard Base64 encoding
/// engine.
///
/// # Note
///
/// You may **not** change the signature of this function.
///
fn read_from_b64_file(file_name: &str) -> Vec<u8> {
    let contents = fs::read_to_string(file_name).unwrap();
    BASE64_STANDARD.decode(contents.trim()).unwrap()
}

/// Returns a tuple containing a randomly generated secret key and public key.
///
/// The secret key is a StaticSecret that can be used in a Diffie-Hellman key
/// exchange. The public key is the associated PublicKey for the StaticSecret.
/// The output of this function is a tuple of bytes corresponding to these keys.
///
/// # Note
///
/// You may **not** change the signature of this function.
///
fn keygen() -> ([u8; 32], [u8; 32]) {
    // TODO
    let secret = StaticSecret::random_from_rng(OsRng);
    let public = PublicKey::from(&secret);
    (secret.to_bytes(), public.to_bytes())
}

/// Returns the encryption of plaintext data to be sent from a sender to a receiver.
///
/// This function performs a Diffie-Hellman key exchange between the sender's
/// secret key and the receiver's public key. Then, the function uses SHA-256 to
/// derive a symmetric encryption key, which is then used in an AES-256-GCM
/// encryption operation. The output vector contains the ciphertext with the
/// AES-256-GCM nonce (12 bytes long) appended to its end.
///
/// # Arguments
///
/// * `input` - A vector of bytes (`u8`) that represents the plaintext data to be encrypted.
/// * `sender_sk` - An array of bytes representing the secret key of the sender.
/// * `receiver_pk` - An array of bytes representing the public key of the receiver.
///
/// # Note
///
/// You may **not** change the signature of this function.
///
fn encrypt(input: Vec<u8>, sender_sk: [u8; 32], receiver_pk: [u8; 32]) -> Vec<u8> {
    let sender_secret = StaticSecret::from(sender_sk);
    let receiver_public = PublicKey::from(receiver_pk);
    let shared_secret = sender_secret.diffie_hellman(&receiver_public);
    
    let mut hasher = Sha256::new();
    hasher.update(shared_secret.as_bytes());
    let key_bytes = hasher.finalize();
    
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);
    
    let nonce = Aes256Gcm::generate_nonce(&mut OsRng);
    let ciphertext = cipher.encrypt(&nonce, input.as_ref()).unwrap();
    let mut result = ciphertext;
    result.extend_from_slice(&nonce);
    
    result
}

/// Returns the decryption of ciphertext data to be received by a receiver from a sender.
///
/// This function performs a Diffie-Hellman key exchange between the receiver's
/// secret key and the sender's public key. Then, the function uses SHA-256 to
/// derive a symmetric encryption key, which is then used in an AES-256-GCM
/// decryption operation. The nonce for this decryption is the last 12 bytes of
/// the input. The output vector contains the plaintext.
///
/// # Arguments
///
/// * `input` - A vector of bytes that represents the ciphertext data to be encrypted and the associated nonce.
/// * `receiver_sk` - An array of bytes representing the secret key of the receiver.
/// * `sender_pk` - An array of bytes representing the public key of the sender.
///
/// # Note
///
/// You may **not** change the signature of this function.
///
fn decrypt(input: Vec<u8>, receiver_sk: [u8; 32], sender_pk: [u8; 32]) -> Vec<u8> {
    let receiver_secret = StaticSecret::from(receiver_sk);
    let sender_public = PublicKey::from(sender_pk);
    let shared_secret = receiver_secret.diffie_hellman(&sender_public);

    let mut hasher = Sha256::new();
    hasher.update(shared_secret.as_bytes());
    let key_bytes = hasher.finalize();
    
    let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
    let cipher = Aes256Gcm::new(key);
    
    let (ciphertext, nonce_bytes) = input.split_at(input.len() - 12);
    let nonce = aes_gcm::Nonce::from_slice(nonce_bytes);
    
    cipher.decrypt(nonce, ciphertext).unwrap()

}

/// The main function, which parses arguments and calls the correct cryptographic operations.
///
/// # Note
///
/// **Do not modify this function**.
///
fn main() {
    // Collect command line arguments
    let args: Vec<String> = std::env::args().collect();

    // Command parsing: keygen, encrypt, decrypt
    let cmd = &args[1];
    if cmd == "keygen" {
        // Arguments to the command
        let secret_key = &args[2];
        let public_key = &args[3];

        // Generate a secret and public key for this user
        let (sk_bytes, pk_bytes) = keygen();

        // Save those bytes as Base64 to file
        save_to_file_as_b64(&secret_key, &sk_bytes);
        save_to_file_as_b64(&public_key, &pk_bytes);
    } else if cmd == "encrypt" {
        // Arguments to the command
        let input = &args[2];
        let output = &args[3];
        let sender_sk = &args[4];
        let receiver_pk = &args[5];

        // Read input from file
        // Note that this input is not necessarily Base64-encoded
        let input = fs::read(input).unwrap();

        // Read the base64-encoded secret and public keys from file
        // Need to convert the Vec<u8> from this function into the 32-byte array for each key
        let sender_sk: [u8; 32] = read_from_b64_file(sender_sk).try_into().unwrap();
        let receiver_pk: [u8; 32] = read_from_b64_file(receiver_pk).try_into().unwrap();

        // Call the encryption operation
        let output_bytes = encrypt(input, sender_sk, receiver_pk);

        // Save those bytes as Base64 to file
        save_to_file_as_b64(&output, &output_bytes);
    } else if cmd == "decrypt" {
        // Arguments to the command
        let input = &args[2];
        let output = &args[3];
        let receiver_sk = &args[4];
        let sender_pk = &args[5];

        // Read the Base64-encoded input ciphertext from file
        let input = read_from_b64_file(&input);

        // Read the base64-encoded secret and public keys from file
        // Need to convert the Vec<u8> from this function into the 32-byte array for each key
        let receiver_sk: [u8; 32] = read_from_b64_file(&receiver_sk).try_into().unwrap();
        let sender_pk: [u8; 32] = read_from_b64_file(&sender_pk).try_into().unwrap();

        // Call the decryption operation
        let output_bytes = decrypt(input, receiver_sk, sender_pk);

        // Save those bytes as Base64 to file
        fs::write(output, output_bytes).unwrap();
    } else {
        panic!("command not found!")
    }
}


#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_base64_roundtrip() {
        let data = b"Hello, World!";
        save_to_file_as_b64("test.txt", data);
        let read_data = read_from_b64_file("test.txt");
        assert_eq!(data.to_vec(), read_data);
    }

    #[test]
    fn test_keygen() {
        let (sk, pk) = keygen();
        assert_eq!(sk.len(), 32);
        assert_eq!(pk.len(), 32);
    }

    #[test]
    fn test_encrypt_decrypt() {
        // Generate keys for both parties
        let (alice_sk, alice_pk) = keygen();
        let (bob_sk, bob_pk) = keygen();
        
        // Test message
        let message = b"HUSH-HUSH VERY-HUSH";
        
        // Alice encrypts to Bob
        let encrypted = encrypt(message.to_vec(), alice_sk, bob_pk);
        
        // Bob decrypts from Alice
        let decrypted = decrypt(encrypted, bob_sk, alice_pk);
        
        assert_eq!(message.to_vec(), decrypted);
    }

    #[test]
    fn test_shared_secret_symmetry() {
        // Test that both parties derive the same shared secret
        let (alice_sk, alice_pk) = keygen();
        let (bob_sk, bob_pk) = keygen();
        
        // Alices perspective
        let alice_secret = StaticSecret::from(alice_sk);
        let alice_shared = alice_secret.diffie_hellman(&PublicKey::from(bob_pk));
        
        // Bobs perspective
        let bob_secret = StaticSecret::from(bob_sk);
        let bob_shared = bob_secret.diffie_hellman(&PublicKey::from(alice_pk));
        
        assert_eq!(alice_shared.as_bytes(), bob_shared.as_bytes());
    }
}