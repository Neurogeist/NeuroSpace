from solders.keypair import Keypair
import base58
import os
from dotenv import load_dotenv

def generate_keypair():
    # Generate a new keypair
    keypair = Keypair()
    
    # Get the public key and private key
    public_key = str(keypair.pubkey())
    private_key = base58.b58encode(bytes(keypair)).decode('ascii')
    
    # Save to .env file
    with open('.env', 'a') as f:
        f.write(f"\nPAYER_PUBKEY={public_key}\n")
        f.write(f"PAYER_PRIVATE_KEY={private_key}\n")
    
    print(f"Generated new keypair:")
    print(f"Public Key: {public_key}")
    print(f"Private Key: {private_key}")
    print("\nSaved to .env file")

if __name__ == "__main__":
    generate_keypair() 