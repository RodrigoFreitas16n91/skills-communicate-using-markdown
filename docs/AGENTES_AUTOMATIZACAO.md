# 🤖 Agentes Inteligentes e Automações

> **Versão:** 1.0.0 · **Módulo:** IA e Automação  
> **Tecnologias:** Python 3.12, MCP Protocol, LangChain, CrewAI

---

## 📋 Sumário

1. [Visão Geral dos Agentes](#visão-geral-dos-agentes)
2. [Catálogo de Agentes](#catálogo-de-agentes)
3. [Fluxo de Decisão dos Agentes](#fluxo-de-decisão-dos-agentes)
4. [Automações Disponíveis](#automações-disponíveis)
5. [Protocolo MCP](#protocolo-mcp)
6. [Configuração dos Agentes](#configuração-dos-agentes)

---

## Visão Geral dos Agentes

Os agentes inteligentes são processos autônomos que **observam → decidem → agem** com base em regras e modelos de linguagem (LLMs). Eles eliminam tarefas repetitivas e padronizáveis do fluxo de trabalho.

```mermaid
graph TB
    subgraph ENTRADA["📥 Fontes de Entrada"]
        FILA2[Fila RabbitMQ]
        WEBHOOK[Webhooks de ERPs]
        CRON[Agendamento Cron]
        API_TRIGGER[Gatilho via API]
    end

    subgraph ORQUESTRADOR["🎯 Orquestrador MCP"]
        MCP_CORE[MCP Core\nRoteamento de tarefas]
        CONTEXTO[Gerenciador\nde Contexto]
        MEMORIA[Memória\nde Curto/Longo prazo]
    end

    subgraph AGENTES_CAT["🤖 Agentes Especializados"]
        A_SYNC[Agente\nSincronização]
        A_VALID[Agente\nValidação]
        A_TRANS[Agente\nTransformação]
        A_RELAT[Agente\nRelatorios]
        A_ALERT[Agente\nAlertas]
        A_RECON[Agente\nReconciliação]
    end

    subgraph FERRAMENTAS["🛠️ Ferramentas dos Agentes"]
        TOOL_DB[Tool: Banco de Dados]
        TOOL_ERP[Tool: API ERP/CRM]
        TOOL_EMAIL[Tool: Envio de E-mail]
        TOOL_SLACK3[Tool: Slack]
        TOOL_TRELLO[Tool: Trello API]
    end

    FILA2 --> MCP_CORE
    WEBHOOK --> MCP_CORE
    CRON --> MCP_CORE
    API_TRIGGER --> MCP_CORE

    MCP_CORE --> CONTEXTO
    CONTEXTO --> MEMORIA
    MCP_CORE --> A_SYNC
    MCP_CORE --> A_VALID
    MCP_CORE --> A_TRANS
    MCP_CORE --> A_RELAT
    MCP_CORE --> A_ALERT
    MCP_CORE --> A_RECON

    A_SYNC --> TOOL_DB
    A_SYNC --> TOOL_ERP
    A_RELAT --> TOOL_EMAIL
    A_ALERT --> TOOL_SLACK3
    A_RECON --> TOOL_TRELLO

    style ENTRADA fill:#e3f2fd
    style ORQUESTRADOR fill:#e8f5e9
    style AGENTES_CAT fill:#fff3e0
    style FERRAMENTAS fill:#f3e5f5
```

---

## Catálogo de Agentes

### 🔄 Agente de Sincronização

**Propósito:** Mantém dados consistentes entre ERP/CRM e o banco local.

```mermaid
sequenceDiagram
    participant CRON2 as ⏰ Cron (5 min)
    participant A_S as 🤖 Agente Sincronização
    participant ERP2 as 🏢 ERP
    participant DB2 as 💾 Banco Local
    participant FILA3 as 📨 Fila de Eventos

    CRON2->>A_S: Dispara sincronização
    A_S->>DB2: Consulta última sincronização
    DB2-->>A_S: timestamp: 2026-05-08T03:52:57Z
    A_S->>ERP2: GET /pedidos?desde=2026-05-08T03:52:57Z
    ERP2-->>A_S: [{pedido_1}, {pedido_2}, {pedido_3}]
    A_S->>A_S: Valida e normaliza 3 pedidos
    A_S->>DB2: UPSERT 3 pedidos normalizados
    A_S->>FILA3: Publica evento "pedidos_sincronizados"
    A_S->>DB2: Atualiza timestamp da última sync
```

| Propriedade | Valor |
|---|---|
| Frequência | A cada 5 minutos (configurável) |
| Timeout máximo | 120 segundos |
| Retry em falha | 3 tentativas com backoff |
| Saída em caso de erro | Dead Letter Queue + alerta Slack |

---

### ✅ Agente de Validação

**Propósito:** Garante a qualidade e integridade dos dados antes da persistência.

```mermaid
flowchart TD
    DADO([Dado recebido]) --> V1{CNPJ/CPF válido?}
    V1 -->|Não| REJEITA_1[Rejeita: CNPJ inválido]
    V1 -->|Sim| V2{Campos obrigatórios\npresentes?}
    V2 -->|Não| REJEITA_2[Rejeita: campo ausente]
    V2 -->|Sim| V3{Valores numéricos\ncoerentes?}
    V3 -->|Não| CORRIGE[Tenta corrigir\nautomaticamente]
    V3 -->|Sim| V4{Duplicidade?}
    CORRIGE --> V4
    V4 -->|Sim| DESCARTA[Descarta: duplicado]
    V4 -->|Não| APROVA([✅ Dado aprovado])

    REJEITA_1 --> DLQ2[Dead Letter Queue]
    REJEITA_2 --> DLQ2

    style APROVA fill:#c8e6c9,stroke:#388E3C
    style DLQ2 fill:#ffcdd2,stroke:#D32F2F
    style DESCARTA fill:#fff9c4
```

**Regras de validação implementadas:**

| Regra | Campo | Ação em caso de falha |
|---|---|---|
| CNPJ/CPF válido | `codigo_cliente` | Rejeição + DLQ |
| Valor > 0 | `valor_total` | Rejeição |
| Data no futuro | `data_entrega` | Alerta (aceita) |
| Duplicidade | `numero_pedido` | Descarte silencioso |
| Moeda suportada | `moeda` | Converte para BRL |

---

### 🔁 Agente de Transformação

**Propósito:** Converte dados entre formatos e estruturas de diferentes sistemas.

```mermaid
graph LR
    subgraph FORMATOS_ENTRADA["Formatos de Entrada"]
        XML[XML SOAP\nTOTVS Legado]
        JSON_IN[JSON REST\nSAP/Oracle]
        CSV[CSV/TXT\nImportação Manual]
        EDI[EDI ANSI X12\nParceiros]
    end

    subgraph MOTOR["Motor de Transformação"]
        PARSER[Parser\nUniversal]
        MAPEADOR[Mapeador\nde Campos]
        CONVERSOR[Conversor\nde Tipos]
        ENRIQUECEDOR[Enriquecedor\nde Dados]
    end

    subgraph SAIDA["Formato de Saída"]
        MODELO_UNI[Modelo\nUnificado JSON]
    end

    XML --> PARSER
    JSON_IN --> PARSER
    CSV --> PARSER
    EDI --> PARSER

    PARSER --> MAPEADOR
    MAPEADOR --> CONVERSOR
    CONVERSOR --> ENRIQUECEDOR
    ENRIQUECEDOR --> MODELO_UNI

    style FORMATOS_ENTRADA fill:#e3f2fd
    style MOTOR fill:#e8f5e9
    style SAIDA fill:#c8e6c9
```

---

### 📊 Agente de Relatórios

**Propósito:** Gera relatórios automatizados e os distribui para stakeholders.

**Relatórios disponíveis:**

| Relatório | Frequência | Destinatários | Formato |
|---|---|---|---|
| Resumo de sincronizações | Diário 07:00h | Time de Operações | E-mail HTML |
| Pedidos do dia | Diário 08:00h | Diretoria Comercial | PDF + E-mail |
| Erros de integração | Sob demanda (P1/P2) | Time de Dev | Slack |
| KPIs semanais | Sexta 17:00h | Gestores | Dashboard Grafana |
| Compliance LGPD | Mensal | DPO | PDF |

---

### 🚨 Agente de Alertas

**Propósito:** Monitora indicadores e dispara notificações proativas.

```mermaid
flowchart LR
    METRICAS[Métricas\nPrometheus] --> AVALIADOR{Limiar\nexcedido?}
    LOGS[Logs\nElasticsearch] --> AVALIADOR
    HEALTH[Health\nChecks] --> AVALIADOR

    AVALIADOR -->|Sim| CLASSIFICA{Classifica\ngravidade}
    AVALIADOR -->|Não| IGNORA[Ignora]

    CLASSIFICA -->|P1 Crítico| ACAO_P1[Liga + Slack + E-mail\nAbrir incidente]
    CLASSIFICA -->|P2 Alto| ACAO_P2[Slack + E-mail\nTicket Trello]
    CLASSIFICA -->|P3/P4| ACAO_P3[Ticket Trello]

    style ACAO_P1 fill:#ffcdd2
    style ACAO_P2 fill:#fff9c4
    style ACAO_P3 fill:#e8f5e9
```

---

### ⚖️ Agente de Reconciliação

**Propósito:** Detecta e corrige inconsistências entre sistemas.

```mermaid
graph TB
    INICIO2([Início da Reconciliação]) --> BUSCA_LOCAL[Busca dados\nbanco local]
    BUSCA_LOCAL --> BUSCA_ERP[Busca dados\nno ERP]
    BUSCA_ERP --> COMPARA{Dados\ndivergem?}
    COMPARA -->|Não| OK([✅ Consistente])
    COMPARA -->|Sim| ANALISA{Qual fonte\né autoritativa?}
    ANALISA -->|ERP é fonte| ATUALIZA_LOCAL[Atualiza\nbanco local]
    ANALISA -->|Local é fonte| ATUALIZA_ERP[Envia correção\nao ERP]
    ANALISA -->|Ambíguo| ESCALONA[Cria ticket\npara revisão manual]
    ATUALIZA_LOCAL --> LOG_RECON[Registra reconciliação]
    ATUALIZA_ERP --> LOG_RECON
    ESCALONA --> LOG_RECON
    LOG_RECON --> OK2([Fim])
```

---

## Automações Disponíveis

### Mapa de Automações

```mermaid
mindmap
  root((Automações))
    Financeiro
      Conciliação bancária automática
      Alertas de inadimplência
      Geração de boletos
      Fechamento mensal
    Comercial
      Sincronização de pedidos
      Follow-up automático de propostas
      Atualização de status no CRM
      Geração de relatório de vendas
    Estoque
      Alertas de estoque mínimo
      Pedidos automáticos de reposição
      Reconciliação de inventário
    TI e Operações
      Deploy automático via CI/CD
      Backup e verificação
      Limpeza de logs antigos
      Renovação de certificados SSL
    RH
      Relatório de ponto eletrônico
      Onboarding de novos usuários
      Desativação de acessos
```

### Catálogo de Automações

| # | Automação | Gatilho | Agente | Tempo Economizado |
|---|---|---|---|---|
| A-001 | Sync pedidos ERP→Local | Cron 5min | Sincronização | ~4h/dia |
| A-002 | Validação de cadastros | Evento de novo cliente | Validação | ~2h/dia |
| A-003 | Relatório diário de vendas | Cron 07:00h | Relatórios | ~1h/dia |
| A-004 | Alerta estoque mínimo | Evento de saída de estoque | Alertas | ~30min/dia |
| A-005 | Reconciliação semanal | Cron domingo 01:00h | Reconciliação | ~6h/semana |
| A-006 | Onboarding de usuário | Webhook RH | Validação | ~45min/usuário |
| A-007 | Renovação token OAuth | Cron pré-expiração | Sincronização | Eliminação de erros |

---

## Protocolo MCP

O **Model Context Protocol (MCP)** é o protocolo central que permite aos agentes se comunicarem com ferramentas externas e compartilharem contexto.

```mermaid
graph LR
    subgraph HOST["Host MCP"]
        CLIENTE_MCP[Cliente MCP\n(nossa aplicação)]
    end

    subgraph SERVIDORES["Servidores MCP"]
        SRV_ERP[MCP Server\nERP Tools]
        SRV_DB3[MCP Server\nDatabase Tools]
        SRV_NOTIF[MCP Server\nNotification Tools]
        SRV_FILES[MCP Server\nFile System Tools]
    end

    subgraph TOOLS_MCP["Ferramentas Expostas"]
        T_GET_PEDIDO[get_pedido_erp]
        T_UPDATE_STATUS[update_status_pedido]
        T_SAVE_DB[save_to_database]
        T_QUERY_DB[query_database]
        T_SEND_SLACK[send_slack_message]
        T_SEND_EMAIL[send_email]
    end

    CLIENTE_MCP <-->|JSON-RPC 2.0| SRV_ERP
    CLIENTE_MCP <-->|JSON-RPC 2.0| SRV_DB3
    CLIENTE_MCP <-->|JSON-RPC 2.0| SRV_NOTIF
    CLIENTE_MCP <-->|JSON-RPC 2.0| SRV_FILES

    SRV_ERP --> T_GET_PEDIDO
    SRV_ERP --> T_UPDATE_STATUS
    SRV_DB3 --> T_SAVE_DB
    SRV_DB3 --> T_QUERY_DB
    SRV_NOTIF --> T_SEND_SLACK
    SRV_NOTIF --> T_SEND_EMAIL

    style HOST fill:#e3f2fd
    style SERVIDORES fill:#e8f5e9
    style TOOLS_MCP fill:#fff3e0
```

### Exemplo de Chamada MCP

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_pedido_erp",
    "arguments": {
      "sistema_origem": "TOTVS",
      "numero_pedido": "000123",
      "incluir_itens": true
    }
  }
}
```

---

## Configuração dos Agentes

### Variáveis de Ambiente dos Agentes

```env
# Configurações gerais dos agentes
MCP_SERVIDOR_URL=http://mcp-servidor:8000
MCP_TOKEN_ACESSO=seu_token_aqui

# Modelo de linguagem (LLM)
LLM_PROVEDOR=openai
LLM_MODELO=gpt-4o-mini
LLM_CHAVE_API=sk-...

# Agente de Sincronização
SYNC_INTERVALO_MINUTOS=5
SYNC_TAMANHO_LOTE=100
SYNC_TENTATIVAS_MAXIMAS=3

# Agente de Alertas
ALERTA_SLACK_WEBHOOK=https://hooks.slack.com/...
ALERTA_EMAIL_DESTINO=ops@empresa.com
ALERTA_LIMIAR_ERROS=10

# Agente de Relatórios
RELATORIO_EMAIL_SMTP=smtp.empresa.com
RELATORIO_EMAIL_PORTA=587
RELATORIO_EMAIL_USUARIO=relatorios@empresa.com
RELATORIO_EMAIL_SENHA=senha_segura
```
