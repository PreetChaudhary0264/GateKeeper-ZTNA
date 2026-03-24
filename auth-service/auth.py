from jose import jwt, JWTError
from datetime import datetime, timedelta  #curr time nikalna and time diff cal krna
import os

# Ye same secret key honi chahiye
# Jo gateway ki middleware.go mein hai
SECRET_KEY = os.getenv("JWT_SECRET", "ztna-super-secret-key-2024")  #token sign kro and verify krte waqt signature check kro
ALGORITHM = os.getenv("ALGORITHM", "HS256")
TOKEN_EXPIRE_MINUTES = 15  # sirf 15 min!

print("ALGO",ALGORITHM)

def create_token(email: str, role: str, name: str) -> str:
    """
    Ramesh login karta hai →
    ye function uska token banata hai

    Token ke andar:
    - email (kaun hai)
    - role  (kya access hai)
    - expiry (kab tak valid hai)
    """
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": email,       # subject — kaun hai
        "role": role,       # hr / finance / admin
        "name": name,       # display ke liye
        "exp": expire,      # 15 min baad expire
        "iat": datetime.utcnow()  # kab banaya
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)  #list isliye di hai jisse hacker none na bhej paye , bina list ke hacker none bhej skta tha jisse no signature verification
    print(f"Token created for {email} | Role: {role} | Expires: {expire}")
    return token


def verify_token(token: str) -> dict:
    """
    Gateway jab bhi request aaye —
    ye function token verify karta hai

    Return karta hai:
    - valid token → user ki info
    - invalid/expired → error
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        email = payload.get("sub")
        role = payload.get("role")
        name = payload.get("name")

        if not email or not role:
            raise JWTError("Token mein email ya role nahi hai")

        print(f"Token valid — {email} | {role}")
        return {
            "valid": True,
            "email": email,
            "role": role,
            "name": name
        }

    except JWTError as e:
        print(f"Token invalid — {str(e)}")   #error raise isliye kra hai taki main.py ko mil ske wrna error yhi rh jata and unsuccessful login me bhi main.py success login dikhata
        raise


def decode_token_without_verify(token: str) -> dict:
    """
    Token decode karo WITHOUT signature verification
    Used for logout to get expiry time
    """
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload
    except Exception as e:
        raise JWTError(f"Token decode failed: {str(e)}")