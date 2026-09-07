# Análise de Integração Frontend Admin ↔ Backend FastAPI

Após análise das documentações do backend (`Documentação da API — Plataforma Gezi.md` e `endpoints_guide.md`) e do estado actual do painel administrativo, este documento mapeia o que já é possível consumir da API e o que precisamos de adicionar/documentar no backend para suportar todas as funcionalidades do painel.

## 1. O que JÁ podemos consumir (Disponível)

Os seguintes endpoints administrativos já estão planeados/documentados no backend e podem ser integrados no painel imediatamente:

### Dashboard (Métricas)
- **`GET /admin/metrics`**: Fornece os KPIs gerais como total de contadores, contadores online, receita total de hoje, comandos falhados e latência média. Perfeito para os `KpiCard` do topo.
- **`GET /admin/alerts`**: Útil para mostrar notificações ou uma lista de alertas operacionais críticos no dashboard.

### Contadores
- **`GET /admin/meters`**: Retorna a lista de todos os contadores do sistema.
- **`POST /iot/commands/cut-supply`** e **`POST /iot/commands/restore-supply`**: Permitem ao admin realizar o corte ou religação remota de energia de um contador específico.

### Transações
- **`GET /admin/transactions`**: Lista as transações financeiras com filtros (`status`, `from`, `to`, `meter_id`), essencial para a página de transações do admin.

### Utilizadores
- **`GET /admin/users`**: Lista os utilizadores.

---

## 2. O que FALTA (Gaps para documentar/desenvolver no Backend)

Para o painel administrativo funcionar a 100% como no design original (que tinha mock data), as seguintes funcionalidades/endpoints estão em falta no backend:

### 2.1. Dashboard (Gráficos)
- **Falta:** Um endpoint para obter dados históricos (ex: diários ou semanais) de receitas e número de transações para desenhar os gráficos (como o `weeklyTxData` que existia no mock).
  - *Sugestão:* Adicionar um endpoint `GET /admin/metrics/history?period=7d` ou adaptar o `GET /admin/transactions` para fazer agregações.

### 2.2. Contadores (Gestão Completa)
- **Falta:** Detalhes completos na listagem de contadores. A resposta actual de `GET /admin/meters` só retorna `status` e `credit_kwh`. Precisamos de dados como `owner`, `phone`, `location`, `serial_number`, e `lastSync`.
- **Falta:** Permissão de Admin para editar contadores de qualquer utilizador. O `PATCH /meters/{id}` actual parece estar restrito aos donos. Precisamos garantir que administradores podem invocar uma rota como `PATCH /admin/meters/{id}`.

### 2.3. Módulos IoT (Dispositivos Físicos)
- **Falta:** Endpoint para listar módulos IoT detalhados. A documentação menciona gerir a telemetria, mas não tem um endpoint como **`GET /admin/iot-modules`** que liste: `firmware_version`, `ip_address`, `signal_strength`, `uptime`, e o vínculo com o `meter_id`.
- **Falta:** Comandos de administração IoT, como forçar atualização de firmware OTA ou reiniciar o módulo (`REBOOT`).

### 2.4. Transações (Detalhes)
- **Falta:** O endpoint `GET /admin/transactions` precisa retornar mais dados na resposta. O schema actual não inclui quem fez a recarga (user), método de pagamento (`M-Pesa`, `e-Mola`) e os `kwh` adquiridos (retorna apenas o montante).

### 2.5. Gestão de Utilizadores e Papéis (RBAC)
- **Falta:** Como vamos criar novos administradores (Admins, Viewers)? Precisamos de um endpoint **`POST /admin/users`** que crie o utilizador no Supabase e atribua a role (papel) adequada.
- **Falta:** Activar/Desactivar acesso de um administrador (ex: **`PATCH /admin/users/{id}/status`**).

### 2.6. Auditoria (Logs do Sistema)
- **Falta:** Endpoint **`GET /admin/audit-logs`**. O painel precisa visualizar quem fez o quê (ex: "Admin X forçou o corte de energia no contador Y", "Admin Z fez login"). O backend já regista comandos em `command_log`, mas precisamos de um registo central de auditoria para acções do sistema.

---

## 3. Integração Supabase vs FastAPI (.env.local)

As variáveis no `.env.local` que providenciaste estão correctas para a configuração do lado do Admin (cliente e servidor web):

```env
SUPABASE_URL="https://ffhfzxzpysyeuhmrzecq.supabase.co"
SUPABASE_KEY="sb_publishable_TBqYyAr9zUXVXxRoNd6JtQ_eIPwM0r-"
API_BASE_URL="gezi.up.railway.app"
```
**Nota sobre o `API_BASE_URL`**: Falta o protocolo (`https://`) na variável. Deverá ser ajustado para:
`NEXT_PUBLIC_FASTAPI_URL="https://gezi.up.railway.app/v1"` para o nosso wrapper funcionar correctamente.
Também recomendo prefixar as variáveis do Supabase com `NEXT_PUBLIC_` para ficarem expostas ao browser client (Shadcn components, etc):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
