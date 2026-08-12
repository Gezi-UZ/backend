# Gezi Backend API

O backend da Plataforma Gezi, responsável pela orquestração do sistema de recargas remotas CREDELEC via IoT. Construído com **FastAPI**, estruturado em **Clean Architecture**, e orquestrado via **Docker**.

## Sobre o projecto

O sistema Gezi moderniza o processo de recarga de energia eléctrica pré-paga da Electricidade de Moçambique (EDM). A plataforma integra:
- **Aplicação Móvel (Flutter)**: Interface do utilizador.
- **Backend (FastAPI)**: Orquestrador de regras de negócio, integrações externas e pagamentos.
- **Supabase**: Base de dados PostgreSQL (com SQLAlchemy/Alembic) e Servidor Realtime para WebSockets directos ao mobile, além de gestão de Autenticação (Auth).
- **MQTT Broker (HiveMQ)**: Comunicação assíncrona com os dispositivos IoT (ESP32).
- **E2Payments**: Integração com M-Pesa para transacções financeiras.

## Arquitectura

Seguimos os princípios da **Clean Architecture**, com separação clara de responsabilidades:
- `app/api/`: Controladores (routers) REST.
- `app/core/`: Configurações centrais, segurança, clientes base (Supabase, MQTT).
- `app/domain/`: Modelos de dados e schemas Pydantic.
- `app/use_cases/`: Regras de negócio (ex: processar recarga).
- `app/infrastructure/`: Adaptadores externos (Bases de Dados, Gateways de Pagamento).

## Setup e Instalação

### Pré-requisitos
- [Docker](https://www.docker.com/) e Docker Compose
- [uv](https://github.com/astral-sh/uv) (Gestor de pacotes Python super-rápido)
- Python 3.11+

### Desenvolvimento local

1. Instalar dependências usando o `uv`:
   ```bash
   uv pip install -r pyproject.toml
   ```
2. Configurar variáveis de ambiente:
   ```bash
   cp .env.example .env
   # Preencha os valores reais no ficheiro .env
   ```
3. Executar o servidor localmente:
   ```bash
   uvicorn app.main:app --reload
   ```

Ou usando **Docker**:
```bash
docker-compose up --build
```

A documentação interactiva da API (Swagger UI) estará disponível em: `http://localhost:8000/docs`.

## Migrações da base de dados (Alembic)

Para garantir máxima performance, utilizamos SQLAlchemy core e Alembic para as migrações:
```bash
alembic revision --autogenerate -m "descricao"
alembic upgrade head
```

## Comunicação em tempo real

A comunicação síncrona HTTP é gerida pelo FastAPI. Para actualizações de estado em tempo real (ex: consumo do contador, confirmação de recarga) para a aplicação móvel, o backend grava as alterações no **Supabase PostgreSQL** e o **Supabase Realtime** envia directamente essas actualizações para o cliente Mobile via WebSockets, garantindo a menor latência possível.

## Autenticação

A autenticação do utilizador (login/OTP) é feita **directamente do Mobile para o Supabase Auth**, reduzindo a latência. O backend recebe apenas o token JWT no cabeçalho `Authorization` dos pedidos REST e valida-o de forma segura.
