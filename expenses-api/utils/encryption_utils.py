import bcrypt

def generate_hash(text:bytes):
    return bcrypt.hashpw(text,bcrypt.gensalt())

def check_pass(password:bytes,hashed:bytes):
    return bcrypt.checkpw(password=password,hashed_password=hashed)