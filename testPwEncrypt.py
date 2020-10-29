from passlib.context import CryptContext

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

def encrypt_password(password):
    return pwd_context.hash(password)


def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)

print(encrypt_password("d1"))
h = encrypt_password("d1")
print(check_encrypted_password("d1",h))
print(check_encrypted_password("d2",h))
