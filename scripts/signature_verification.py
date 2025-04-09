from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

# 🔒 Backend signer address (replace with your actual signer)
EXPECTED_SIGNER = "0xF1A960a8d0CA410fF7a41b64aEdaAcA6Ad0e290b"

# 🧾 Values returned from your API
verification_hash = "872d809e86652959453343b43c22b06c4e41979d6e453e23d7f36199183a3534"
signature = "0xa0602bae6ed39ae03aafac9e7f088d0b9b498444f86e965789a80fbe4ec1929e342d77dfe2f81c305a453e9dd8c169091aff7d97c7885bb41d205b0b483b98cf1c"

# 🧠 Prepare message object for EIP-191
message = encode_defunct(hexstr=verification_hash)

# 🔍 Recover address from signature
recovered_address = Account.recover_message(message, signature=signature)

print(f"Recovered address: {recovered_address}")

# ✅ Check if signature is valid
if Web3.to_checksum_address(recovered_address) == Web3.to_checksum_address(EXPECTED_SIGNER):
    print("✅ Signature is VALID and matches the expected signer.")
else:
    print("❌ Signature is INVALID or signed by a different address.")
