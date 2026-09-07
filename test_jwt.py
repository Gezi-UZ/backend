import jwt
from jwt.exceptions import InvalidAlgorithmError

# Case 1: Token is HS256, but we expect RS256
token_hs256 = jwt.encode({"test": 1}, "secret", algorithm="HS256")
try:
    jwt.decode(token_hs256, "secret", algorithms=["RS256"])
except Exception as e:
    print(f"Case 1 Error: {str(e)} ({type(e)})")

# Case 2: Token is RS256, but we expect HS256
import cryptography.hazmat.primitives.asymmetric.rsa as rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()
private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
public_pem = public_key.public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)

token_rs256 = jwt.encode({"test": 1}, private_pem, algorithm="RS256")
try:
    jwt.decode(token_rs256, "secret", algorithms=["HS256"])
except Exception as e:
    print(f"Case 2 Error: {str(e)} ({type(e)})")

