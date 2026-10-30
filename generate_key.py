from crypto import generate_master_key

print("Your new MASTER_KEY (copy this into your .env file):")
print()
print(generate_master_key())
print()
print("Back it up somewhere safe. If you lose it, your encrypted files can NEVER be recovered.")