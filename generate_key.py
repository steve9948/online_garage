import secrets
import string

#Python script for generating secret keys
def generate_secret_key():
    chars = string.ascii_lowercase + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(chars) for _ in range(50))

print(generate_secret_key())