# 🏗️ Arquitetura do Sistema de Integrações ERP/CRM com MCP e Docker

> **Versão:** 1.0.0 · **Data:** 2026-05-08 · **Autor:** Rodrigo Freitas  
> **Status:** Em desenvolvimento

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Diagrama de Arquitetura Geral](#diagrama-de-arquitetura-geral)
3. [Componentes Principais](#componentes-principais)
4. [Fluxo de Dados](#fluxo-de-dados)
5. [Camadas da Aplicação](#camadas-da-aplicação)
6. [Infraestrutura com Docker](#infraestrutura-com-docker)
7. [Segurança e Governança](#segurança-e-governança)
8. [Escalabilidade](#escalabilidade)
9. [Tecnologias Utilizadas](#tecnologias-utilizadas)

---

## Visão Geral

O sistema é uma **plataforma de integração inteligente** que conecta ERPs e CRMs corporativos (TOTVS, SAP, Oracle) por meio de uma camada MCP (Model Context Protocol) orquestrada via Docker. Agentes de inteligência artificial automatizam tarefas repetitivas, enquanto pipelines CI/CD garantem entregas contínuas e governança de T.I.

```
┌──────────────────────────────────────────────────────────────────────┐
│                    PLATAFORMA DE INTEGRAÇÃO INTELIGENTE              │
│                                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │
│  │  TOTVS   │   │   SAP    │   │  ORACLE  │   │  Outros Sistemas │ │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────────┬─────────┘ │
│       │              │              │                    │           │
│       └──────────────┴──────────────┴────────────────────┘           │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │  CAMADA MCP/API   │                            │
│                    │  (Orquestrador)   │                            │
│                    └─────────┬─────────┘                            │
│                              │                                       │
│          ┌───────────────────┼───────────────────┐                  │
│          │                   │                   │                  │
│  ┌───────▼───────┐  ┌────────▼──────┐  ┌────────▼────────┐        │
│  │   Agentes IA  │  │  Automações   │  │  Governança T.I │        │
│  └───────┬───────┘  └────────┬──────┘  └────────┬────────┘        │
│          │                   │                   │                  │
│          └───────────────────┴───────────────────┘                  │
│                              │                                       │
│                    ┌─────────▼─────────┐                            │
│                    │   DOCKER/K8s      │                            │
│                    │  (Infraestrutura) │                            │
│                    └───────────────────┘                            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Diagrama de Arquitetura Geral

```mermaid
graph TB
    subgraph FONTES["🏢 Sistemas de Origem"]
        TOTVS[TOTVS Protheus]
        SAP[SAP ERP]
        ORACLE[Oracle ERP Cloud]
        CRM[CRMs Externos]
    end

    subgraph MCP["🔌 Camada MCP - Orquestrador"]
        GATEWAY[API Gateway]
        AUTENTICACAO[Autenticação OAuth2/JWT]
        ROTEADOR[Roteador de Mensagens]
        FILA[Fila de Mensagens - RabbitMQ]
    end

    subgraph AGENTES["🤖 Agentes Inteligentes"]
        AGENTE_SYNC[Agente de Sincronização]
        AGENTE_VALID[Agente de Validação]
        AGENTE_TRANS[Agente de Transformação]
        AGENTE_MON[Agente de Monitoramento]
    end

    subgraph DADOS["💾 Camada de Dados"]
        POSTGRES[(PostgreSQL)]
        REDIS[(Redis Cache)]
        ELASTIC[(Elasticsearch - Logs)]
    end

    subgraph INFRA["🐳 Docker / Kubernetes"]
        CONTAINER1[Container: MCP Server]
        CONTAINER2[Container: Agentes]
        CONTAINER3[Container: Banco de Dados]
        CONTAINER4[Container: Monitoramento]
    end

    subgraph GOV["📊 Governança e Observabilidade"]
        KIBANA[Kibana - Dashboards]
        GRAFANA[Grafana - Métricas]
        TRELLO[Trello - Gestão Ágil]
    end

    TOTVS --> GATEWAY
    SAP --> GATEWAY
    ORACLE --> GATEWAY
    CRM --> GATEWAY

    GATEWAY --> AUTENTICACAO
    AUTENTICACAO --> ROTEADOR
    ROTEADOR --> FILA

    FILA --> AGENTE_SYNC
    FILA --> AGENTE_VALID
    FILA --> AGENTE_TRANS

    AGENTE_SYNC --> POSTGRES
    AGENTE_VALID --> REDIS
    AGENTE_TRANS --> POSTGRES
    AGENTE_MON --> ELASTIC

    CONTAINER1 -.->|hospeda| GATEWAY
    CONTAINER2 -.->|hospeda| AGENTE_SYNC
    CONTAINER3 -.->|hospeda| POSTGRES
    CONTAINER4 -.->|hospeda| KIBANA

    ELASTIC --> KIBANA
    POSTGRES --> GRAFANA
    GRAFANA --> TRELLO

    style FONTES fill:#e8f4fd,stroke:#2196F3
    style MCP fill:#e8f5e9,stroke:#4CAF50
    style AGENTES fill:#fff3e0,stroke:#FF9800
    style DADOS fill:#f3e5f5,stroke:#9C27B0
    style INFRA fill:#fce4ec,stroke:#E91E63
    style GOV fill:#e0f2f1,stroke:#009688
```

---

## Componentes Principais

### 1. 🔌 Camada MCP (Model Context Protocol)

| Componente | Função | Tecnologia |
|---|---|---|
| API Gateway | Ponto único de entrada de requisições | Kong / Nginx |
| Autenticação | Validação de identidade e permissões | OAuth2 + JWT |
| Roteador | Direciona mensagens ao destino correto | RabbitMQ |
| Transformador | Converte formatos entre sistemas | Python / Jinja2 |

### 2. 🤖 Agentes Inteligentes

| Agente | Responsabilidade |
|---|---|
| `AgenteIntegracao` | Sincroniza dados entre ERP e CRM |
| `AgenteValidacao` | Valida e higieniza dados antes da persistência |
| `AgenteTransformacao` | Mapeia campos e transforma estruturas de dados |
| `AgenteMonitoramento` | Detecta anomalias e gera alertas |

### 3. 🐳 Infraestrutura Docker

Cada serviço roda em container isolado, garantindo:
- **Portabilidade**: funciona igual em qualquer ambiente
- **Isolamento**: falha de um serviço não afeta outros
- **Escalabilidade**: scale horizontal via `docker-compose scale`

---

## Fluxo de Dados

```mermaid
sequenceDiagram
    participant ERP as 🏢 ERP (TOTVS/SAP)
    participant GW as 🔌 API Gateway
    participant AUTH as 🔐 Autenticação
    participant FILA as 📨 Fila de Mensagens
    participant AGENTE as 🤖 Agente Inteligente
    participant DB as 💾 Banco de Dados
    participant MONITOR as 📊 Monitoramento

    ERP->>GW: Envia evento (ex: novo pedido)
    GW->>AUTH: Valida token JWT
    AUTH-->>GW: Token válido ✅
    GW->>FILA: Publica mensagem na fila
    FILA->>AGENTE: Consome mensagem
    AGENTE->>AGENTE: Valida e transforma dados
    AGENTE->>DB: Persiste dados processados
    AGENTE->>MONITOR: Registra log do evento
    MONITOR-->>ERP: Confirmação de processamento ✅
```

---

## Camadas da Aplicação

```mermaid
graph LR
    subgraph APRESENTACAO["Camada de Apresentação"]
        API_REST[API REST]
        WEBHOOKS[Webhooks]
        SWAGGER[Swagger UI]
    end

    subgraph NEGOCIO["Camada de Negócio"]
        REGRAS[Regras de Negócio]
        VALIDACOES[Validações]
        MAPEAMENTOS[Mapeamentos]
    end

    subgraph INTEGRACAO_CAM["Camada de Integração"]
        CONECTORES[Conectores ERP/CRM]
        ADAPTADORES[Adaptadores de Protocolo]
        TRANSFORMADORES[Transformadores de Dados]
    end

    subgraph PERSISTENCIA["Camada de Persistência"]
        ORM[ORM SQLAlchemy]
        CACHE[Cache Redis]
        MIGRACAO[Migrações Alembic]
    end

    APRESENTACAO --> NEGOCIO
    NEGOCIO --> INTEGRACAO_CAM
    INTEGRACAO_CAM --> PERSISTENCIA

    style APRESENTACAO fill:#e3f2fd
    style NEGOCIO fill:#e8f5e9
    style INTEGRACAO_CAM fill:#fff8e1
    style PERSISTENCIA fill:#fce4ec
```

---

## Infraestrutura com Docker

```mermaid
graph TB
    subgraph REDE_DOCKER["🐳 Rede Docker: rede-integracao"]
        subgraph SERVICOS_APP["Serviços de Aplicação"]
            MCP_SERVER[mcp-servidor\nPorta: 8000]
            AGENTE_SVC[agentes-servico\nPorta: 8001]
            WORKER[worker-filas\nPorta: -]
        end

        subgraph SERVICOS_DADOS["Serviços de Dados"]
            PG[postgres\nPorta: 5432]
            RD[redis\nPorta: 6379]
            RMQ[rabbitmq\nPorta: 5672/15672]
        end

        subgraph SERVICOS_OBS["Serviços de Observabilidade"]
            ELK[elasticsearch\nPorta: 9200]
            KIB[kibana\nPorta: 5601]
            GRF[grafana\nPorta: 3000]
        end
    end

    MCP_SERVER <--> PG
    MCP_SERVER <--> RD
    MCP_SERVER <--> RMQ
    AGENTE_SVC <--> RMQ
    AGENTE_SVC <--> PG
    WORKER <--> RMQ
    MCP_SERVER --> ELK
    AGENTE_SVC --> ELK
    ELK --> KIB
    PG --> GRF
```

---

## Segurança e Governança

| Camada | Controle | Ferramenta |
|---|---|---|
| Autenticação | JWT + OAuth 2.0 | Keycloak |
| Autorização | RBAC (por perfil) | Políticas customizadas |
| Secrets | Variáveis de ambiente seguras | Docker Secrets / Vault |
| Auditoria | Log de todas as ações | Elasticsearch |
| Rede | Comunicação criptografada | TLS 1.3 |
| Vulnerabilidades | Scan de imagens Docker | Trivy |

---

## Escalabilidade

```mermaid
graph LR
    LB[Load Balancer\nNginx] --> I1[Instância 1\nMCP Server]
    LB --> I2[Instância 2\nMCP Server]
    LB --> I3[Instância N\nMCP Server]
    I1 --> PG_MASTER[(PostgreSQL\nMaster)]
    I2 --> PG_MASTER
    I3 --> PG_MASTER
    PG_MASTER --> PG_REPLICA[(PostgreSQL\nRéplica)]
    I1 --> RD_CLUSTER[(Redis\nCluster)]
    I2 --> RD_CLUSTER
    I3 --> RD_CLUSTER
```

**Estratégia de escala:**
- **Horizontal**: adicionar mais containers via `docker-compose scale mcp-servidor=3`
- **Vertical**: ajustar `resources.limits` no `docker-compose.yml`
- **Cache**: Redis reduz carga no banco em até 80%
- **Filas**: RabbitMQ desacopla produtores de consumidores

---

## Tecnologias Utilizadas

| Categoria | Tecnologia | Versão |
|---|---|---|
| Linguagem | Python | 3.12+ |
| Framework API | FastAPI | 0.110+ |
| ORM | SQLAlchemy + Alembic | 2.0+ |
| Banco de Dados | PostgreSQL | 16+ |
| Cache | Redis | 7+ |
| Mensageria | RabbitMQ | 3.13+ |
| Containerização | Docker + Docker Compose | 26+ |
| Orquestrador (prod) | Kubernetes | 1.30+ |
| Logs | Elasticsearch + Kibana | 8+ |
| Métricas | Grafana + Prometheus | 10+ |
| CI/CD | GitHub Actions | - |
| Gestão Ágil | Trello | - |
| Protocolo IA | MCP (Model Context Protocol) | 1.0+ |
