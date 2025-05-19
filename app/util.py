from passlib.context import CryptContext

pwd_context = CryptContext(schemes = ["bcrypt"], deprecated = "auto")

def password_encrypt(password):
    return pwd_context.hash(password)

def password_verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)