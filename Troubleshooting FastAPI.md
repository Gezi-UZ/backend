# Troubleshooting FastAPI e Supabase JWT (Erros 401)

Se a sua app móvel envia o token corretamente, mas o seu backend FastAPI responde com `401 Unauthorized`, o problema está na validação do token JWT.

Aqui estão os pontos a verificar no código da sua API FastAPI e no seu ambiente da Railway.

## 1. O `SUPABASE_JWT_SECRET` tem de estar correto

A causa número um deste erro é o Backend estar a tentar validar o Token JWT com a "Secret" errada.

1. Vá ao **Dashboard do Supabase**: `Project Settings` > `API`.
2. Encontre a **JWT Secret**.
3. Vá ao **Dashboard do Railway**, ao seu serviço do backend, e na secção `Variables` verifique se a variável `SUPABASE_JWT_SECRET` tem exatamente o mesmo valor.

> [!WARNING]
> Se alterou recentemente a JWT Secret no Supabase, certifique-se de que reinicia o serviço no Railway para que este assuma a nova chave.

## 2. O Algoritmo JWT

O Supabase assina os tokens JWT utilizando o algoritmo **HS256**.
No seu backend (se estiver a utilizar bibliotecas como `python-jose` ou `PyJWT`), garanta que está a forçar o `algorithms=["HS256"]` no momento do decode.

Exemplo de verificação em FastAPI:
```python
import os
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

security = HTTPBearer()
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET")

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    token = credentials.credentials
    try:
        # Importante: O Algoritmo tem de ser o HS256 e tem de especificar a "audience" como "authenticated" (opcional dependendo da config)
        payload = jwt.decode(
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            options={"verify_aud": False} # A aud do supabase por norma é "authenticated"
        )
        return payload
    except JWTError as e:
        # Se cair aqui, a assinatura falhou ou o token expirou
        print(f"Erro JWT: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
```

## 3. Formato do Authorization Header

A sua app Flutter envia o cabeçalho neste formato:
`Authorization: Bearer <TOKEN>`

Certifique-se de que o backend sabe interpretar esse cabeçalho corretamente e consegue extrair apenas a parte `<TOKEN>`. A classe `HTTPBearer()` do FastAPI já faz isto automaticamente.

## 4. O Token está realmente expirado?

Ocasionalmente, podem haver problemas com relógios desincronizados entre serviços. Verifique (faça log do erro exacto) no backend por que razão o `jwt.decode` está a falhar.
* Falha de assinatura (`Signature verification failed`): O Secret está errado.
* Token expirado (`Signature has expired`): Os servidores podem estar dessincronizados, ou um token super antigo está a ser enviado.

## Teste Rápido
1. Faça log-in na app e retire o seu Token através da consola de debug do Flutter (print).
2. Cole o token no site [jwt.io](https://jwt.io).
3. Verifique se no bloco do **Signature** consegue colar o seu Secret do Supabase para que fique *Signature Verified*. Se não der, o seu secret está efetivamente errado no seu painel.
