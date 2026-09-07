import jwt
import cryptography.hazmat.primitives.asymmetric.rsa as rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
private_pem = private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())

token_rs256 = jwt.encode({"test": 1}, private_pem, algorithm="RS256")
try:
    jwt.decode(token_rs256, "secret_string", algorithms=["RS256"])
except Exception as e:
    print(f"Case 3 Error: {str(e)} ({type(e)})")
