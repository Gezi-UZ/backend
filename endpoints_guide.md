# Integração Mobile ↔ Backend (Gezi API v1)

Este documento detalha **todos os endpoints** do backend Gezi para consumo pelo Flutter via Dio, incluindo os novos endpoints de **SSE (Server-Sent Events)**, **comandos IoT**, e **callback de pagamento**.

**Base URL (desenvolvimento):** `http://10.0.2.2:8000/v1` (Android Emulator)  
**Base URL (produção):** `https://gezi-backend.up.railway.app/v1`

---

## 1. Autenticação (JWT)

**Todos os endpoints protegidos exigem o header:**
```
Authorization: Bearer <access_token_do_supabase>
```

> [!IMPORTANT]
> Configurar um interceptor no Dio que injete automaticamente o token:
> ```dart
> dio.interceptors.add(InterceptorsWrapper(
>   onRequest: (options, handler) async {
>     final session = supabase.auth.currentSession;
>     if (session != null) {
>       options.headers['Authorization'] = 'Bearer ${session.accessToken}';
>     }
>     handler.next(options);
>   },
> ));
> ```

---

## 2. Endpoints de Utilizadores (`/v1/users`) — Web Admin

> [!NOTE]
> No mobile, os dados do utilizador são geridos **diretamente via Supabase** (`supabase_flutter`).
> Estes endpoints existem para o **painel web administrativo** e para sincronizar dados internos.

### 2.1. Sincronizar Registo (Signup Sync)
**POST** `/users/`

**Body:**
```json
{
  "telefone": "+258840000000",
  "nome": "João Silva",
  "papel": "cliente",
  "biometria_activa": false,
  "id": "uuid-do-supabase"
}
```

### 2.2. Obter Perfil
**GET** `/users/me`

### 2.3. Atualizar Perfil
**PUT** `/users/me`

**Body (campos opcionais):**
```json
{
  "nome": "João Silva Editado",
  "biometria_activa": true
}
```

---

## 3. Endpoints de Contadores (`/v1/meters`)

### 3.1. Listar Meus Contadores
**GET** `/meters/me`

**Response `200`:**
```json
[
  {
    "id": "uuid-do-contador",
    "serial_number": "GEZI-00123",
    "label": "Casa Matola",
    "location": {
      "latitude": -25.9692,
      "longitude": 32.5732,
      "address": "Matola Rio"
    },
    "estado": "ONLINE",
    "kwh_saldo": 45.2,
    "estado_rele": true,
    "ultima_recarga": "2026-09-01T14:30:00"
  }
]
```

> [!TIP]
> Para **atualizações em tempo real** do estado do contador (kWh, relé, online/offline), o Flutter deve usar **Supabase Realtime** diretamente:
> ```dart
> supabase
>   .from('contador')
>   .stream(primaryKey: ['id'])
>   .eq('utilizador_id', userId)
>   .listen((data) {
>     // Atualizar UI com novos dados
>   });
> ```
> Isto evita overhead HTTP e garante latência mínima.

### 3.2. Adicionar Novo Contador
**POST** `/meters/`

**Body:**
```json
{
  "serial_number": "GEZI-00124",
  "label": "Casa Cidade",
  "location": {
    "latitude": -25.123,
    "longitude": 32.456,
    "address": "Av. Julius Nyerere"
  }
}
```

### 3.3. Detalhes do Contador
**GET** `/meters/{meter_id}`

### 3.4. Atualizar Contador
**PATCH** `/meters/{meter_id}`

### 3.5. Estado em Tempo Real (One-Shot)
**GET** `/meters/{meter_id}/status`

**Response `200`:**
```json
{
  "estado": "ONLINE",
  "kwh_saldo": 12.5,
  "estado_rele": true,
  "ultima_sincronizacao": "2026-09-03T14:30:00"
}
```

---

## 4. Endpoints de Recargas (`/v1/recharges`)

### 4.1. Iniciar Recarga
**POST** `/recharges/initiate`

**Body:**
```json
{
  "meter_id": "uuid-do-contador",
  "amount_mzn": 150.00
}
```

**Response `201`:**
```json
{
  "success": true,
  "data": {
    "recharge_id": "uuid-da-recarga",
    "status": "PENDENTE_PAGAMENTO",
    "amount_mzn": 150.0,
    "estimated_kwh": 20.5,
    "breakdown": {
      "montante_total": 150.0,
      "val_energia": 115.0,
      "iva": 19.5,
      "divida_paga": 0.0,
      "tx_radio": 8.0,
      "tx_lixo": 7.5,
      "kwh_calculado": 20.5
    }
  }
}
```

### 4.2. Acompanhar Recarga em Tempo Real (SSE)
**GET** `/recharges/{recharge_id}/stream`

> [!IMPORTANT]
> **Este endpoint substitui o polling!** O Flutter abre uma conexão SSE e recebe eventos automaticamente sempre que o estado da recarga muda.

**Fluxo de eventos recebidos:**
```
data: {"event":"status_update","data":{"recharge_id":"...","status":"PENDENTE_PAGAMENTO",...}}

data: {"event":"status_update","data":{"recharge_id":"...","status":"MQTT_SENT","kwh":20.5}}

data: {"event":"status_update","data":{"recharge_id":"...","status":"CONCLUIDA","token":"1234-5678","kwh_applied":20.5}}

data: {"event":"stream_end"}
```

**Implementação no Flutter (Dio):**
```dart
Future<void> streamRechargeStatus(String rechargeId) async {
  final response = await dio.get(
    '/recharges/$rechargeId/stream',
    options: Options(
      responseType: ResponseType.stream,
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache',
      },
    ),
  );

  final stream = response.data.stream as Stream<List<int>>;
  
  await for (final chunk in stream) {
    final lines = utf8.decode(chunk).split('\n');
    for (final line in lines) {
      if (line.startsWith('data: ')) {
        final jsonStr = line.substring(6);
        final event = jsonDecode(jsonStr);
        
        if (event['event'] == 'stream_end') {
          return; // Recarga terminou
        }
        
        // Atualizar estado no BLoC/Provider
        final status = event['data']['status'];
        emit(RechargeStatusChanged(status: status, data: event['data']));
      }
    }
  }
}
```

### 4.3. Consultar Estado (One-Shot, Fallback)
**GET** `/recharges/{recharge_id}/status`

> Mantido como fallback caso o SSE não esteja disponível. Retorna o estado actual da recarga num único pedido.

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "recharge_id": "uuid",
    "status": "CONCLUIDA",
    "token": "1234-5678-9012",
    "applied_at": "2026-09-03T14:35:00"
  }
}
```

### 4.4. Inserir Código Manualmente
**POST** `/recharges/manual-code`

**Body:**
```json
{
  "meter_id": "uuid-do-contador",
  "recharge_code": "4321-8765-1098-7654"
}
```

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "recharge_id": "uuid",
    "status": "CONCLUIDA",
    "credit_kwh": 40.0
  }
}
```

### 4.5. Histórico de Recargas
**GET** `/recharges/history`

**Query params:** `meter_id`, `from`, `to`, `page`, `page_size`

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "recharges": [
      {
        "recharge_id": "uuid",
        "meter_id": "uuid",
        "amount_mzn": 150.0,
        "credit_kwh": 20.5,
        "status": "CONCLUIDA",
        "created_at": "2026-09-02T10:00:00"
      }
    ],
    "pagination": { "page": 1, "page_size": 20, "total": 47 }
  }
}
```

### 4.6. Dashboard (Estatísticas)
**GET** `/recharges/dashboard`

**Query params:** `meter_id`, `period` (`week` | `month` | `year`)

**Response `200`:**
```json
{
  "success": true,
  "data": {
    "total_spent_mzn": 1840.00,
    "total_kwh_purchased": 254.3,
    "average_consumption_kwh_day": 8.4,
    "recharge_count": 12
  }
}
```

---

## 5. Endpoints IoT (`/v1/iot`)

### 5.1. Enviar Comando ao ESP32
**POST** `/iot/meters/{meter_id}/command`

> Envia um comando ao dispositivo ESP32 associado ao contador via MQTT (HiveMQ Cloud).

**Tipos de comando disponíveis:**
| `command_type` | Descrição |
|---|---|
| `APPLY_CREDITS` | Aplica um token STS gerado por recarga (usado internamente, mas disponível para testes) |
| `CUT_SUPPLY` | Corta o fornecimento de energia (desliga o relé) |
| `RESTORE_SUPPLY` | Restaura o fornecimento de energia (liga o relé) |
| `STATUS_REQUEST` | Solicita telemetria imediata |

**Body:**
```json
{
  "command_type": "CUT_SUPPLY",
  "payload": {
    "reason": "MANUAL_ADMIN"
  }
}
```

**Response `201`:**
```json
{
  "command_id": "uuid-do-comando",
  "meter_id": "uuid-do-contador",
  "command_type": "CUT_SUPPLY",
  "status": "ENVIADO",
  "sent_at": "2026-09-03T14:30:00"
}
```

### 5.2. Callback M-Pesa (Server-to-Server)
**POST** `/iot/payments/callback`

> [!CAUTION]
> Este endpoint **NÃO requer JWT**. É chamado diretamente pelo servidor M-Pesa quando um pagamento é confirmado. Em produção, validar IP/assinatura do M-Pesa.

**Body:**
```json
{
  "referencia_mpesa": "MP240903143000",
  "montante": 150.00,
  "estado": "SUCCESS"
}
```

**O que acontece internamente (pipeline automático):**
1. `Pagamento.estado` → `SUCCESS`
2. `Recarga.estado` → `CONFIRMED` → `MQTT_SENT`
3. Cálculo do desdobramento tarifário
4. `ComandoIoT` gravado na BD com `estado = "ENVIADO"`
5. Comando MQTT publicado no HiveMQ → ESP32
6. Evento SSE emitido → Flutter recebe atualização
7. Notifica localmente o user que a recarga foi efetuada

---

## 6. MQTT Tópicos e Formatos (Integração Hardware)

O backend comunica com o hardware via HiveMQ Cloud usando os seguintes tópicos e formatos.

### 6.1 Backend → ESP32 (Comandos)
**Tópico:** `credelec/meter/{meter_id}/cmd`

```json
{
  "command": "APPLY_CREDITS",
  "token": "1234-5678-9012-3456",
  "kwh": 18.2,
  "issued_at": "2026-06-25T14:31:00Z"
}
```

### 6.2 ESP32 → Backend (Telemetria e ACK)
**Telemetria:** `credelec/meter/{meter_id}/telemetry`
```json
{
  "kwh": 12.45,
  "relay": true,
  "voltage": 220.4,
  "current": 2.31,
  "power_w": 509.0,
  "frequency": 50.0,
  "timestamp": "2026-06-25T14:32:00Z"
}
```

**Confirmação (ACK):** `credelec/meter/{meter_id}/ack`
```json
{
  "command_id": "uuid-do-comando",
  "status": "ACK",
  "applied_kwh": 18.2,
  "timestamp": "2026-06-25T14:31:05Z"
}
```

---

## 7. Supabase Realtime (Direto — Sem FastAPI)

Para operações de baixa latência, o Flutter lê **diretamente** do Supabase Realtime:

| Dados | Canal Supabase |
|---|---|
| Estado do contador (kWh, relé, online) | `supabase.from('contador').stream(primaryKey: ['id'])` |
| Alertas de saldo baixo | `supabase.from('alerta').stream(primaryKey: ['id'])` |

> [!NOTE]
> 
> **Database → Replication → Enable** para as tabelas desejadas.

---

## 7. Endpoints Administrativos (`/v1/admin/`)

| Endpoint | Descrição |
|---|---|
| `GET /admin/users` | Listar todos os utilizadores (role: admin) |
| `GET /admin/meters` | Listar todos os contadores (role: admin) |

> Protegidos por RBAC — apenas utilizadores com `papel = "admin"`.

---

## 8. Health Check

**GET** `/health`

```json
{
  "status": "healthy",
  "environment": "production",
  "service": "Gezi API"
}
```
