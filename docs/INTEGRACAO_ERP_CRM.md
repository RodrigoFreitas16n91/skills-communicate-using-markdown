# 🔌 Documentação de Integração com ERPs e CRMs

> **Versão:** 1.0.0 · **Módulo:** Conectores de Integração  
> **Sistemas suportados:** TOTVS Protheus, SAP ERP, Oracle ERP Cloud

---

## 📋 Sumário

1. [Visão Geral das Integrações](#visão-geral-das-integrações)
2. [TOTVS Protheus](#totvs-protheus)
3. [SAP ERP](#sap-erp)
4. [Oracle ERP Cloud](#oracle-erp-cloud)
5. [Mapeamento de Campos](#mapeamento-de-campos)
6. [Tratamento de Erros](#tratamento-de-erros)
7. [Exemplos de Payload](#exemplos-de-payload)

---

## Visão Geral das Integrações

```mermaid
graph LR
    subgraph ERPS["ERPs/CRMs"]
        T[TOTVS\nProtheus]
        S[SAP\nERP]
        O[Oracle\nCloud]
    end

    subgraph CONECTORES["Conectores (Python)"]
        CT[ConectorTOTVS]
        CS[ConectorSAP]
        CO[ConectorOracle]
    end

    subgraph MCP_LAYER["Camada MCP"]
        NORM[Normalizador\nde Dados]
        CACHE_MCP[Cache\nRedis]
        FILA_MCP[Fila\nRabbitMQ]
    end

    subgraph DESTINO["Destino"]
        DB_LOCAL[(Banco\nLocal)]
        API_INT[API\nInterna]
    end

    T --> CT
    S --> CS
    O --> CO

    CT --> NORM
    CS --> NORM
    CO --> NORM

    NORM --> CACHE_MCP
    NORM --> FILA_MCP
    FILA_MCP --> DB_LOCAL
    FILA_MCP --> API_INT

    style ERPS fill:#e3f2fd
    style CONECTORES fill:#e8f5e9
    style MCP_LAYER fill:#fff8e1
    style DESTINO fill:#fce4ec
```

---

## TOTVS Protheus

### Protocolo de Comunicação

O TOTVS Protheus expõe dados via **REST API** (TOTVS Fluig / TOTVS Carol) ou **Web Services SOAP** (versões legadas).

```mermaid
sequenceDiagram
    participant APP as 🖥️ Nossa Aplicação
    participant TOT as 🏢 TOTVS Protheus
    participant AUTH_T as 🔐 TOTVS Auth

    APP->>AUTH_T: POST /oauth/token\n{client_id, client_secret}
    AUTH_T-->>APP: {access_token, expires_in}
    APP->>TOT: GET /api/pedidos\nAuthorization: Bearer {token}
    TOT-->>APP: [{pedido_id, cliente, itens, valor}]
    APP->>APP: Processa e normaliza dados
    APP->>TOT: POST /api/pedidos/confirmar\n{pedido_id, status: "CONFIRMADO"}
    TOT-->>APP: {sucesso: true, mensagem: "Pedido confirmado"}
```

### Endpoints Principais (TOTVS)

| Recurso | Método | URL | Descrição |
|---|---|---|---|
| Pedidos | GET | `/api/pedidos` | Lista pedidos |
| Pedido por ID | GET | `/api/pedidos/{id}` | Detalha pedido |
| Clientes | GET | `/api/clientes` | Lista clientes |
| Produtos | GET | `/api/produtos` | Catálogo de produtos |
| Nota Fiscal | POST | `/api/nf-saida` | Emite NF-e |
| Estoque | GET | `/api/estoque/{produto_id}` | Consulta estoque |

### Configuração (`.env`)

```env
# Credenciais TOTVS
TOTVS_URL_BASE=https://seu-servidor-totvs:8080
TOTVS_USUARIO=usuario_integracao
TOTVS_SENHA=senha_segura
TOTVS_EMPRESA=01
TOTVS_FILIAL=0101
TOTVS_TIMEOUT_SEGUNDOS=30
```

---

## SAP ERP

### Protocolo de Comunicação

O SAP utiliza **OData v4** (SAP S/4HANA) ou **RFC/BAPI** via biblioteca `pyrfc`.

```mermaid
sequenceDiagram
    participant APP as 🖥️ Nossa Aplicação
    participant SAP as 🏢 SAP S/4HANA
    participant ODATA as 📡 SAP OData Service

    APP->>ODATA: GET /sap/opu/odata/sap/API_SALES_ORDER_SRV\n?$filter=CreationDate gt 2026-01-01
    ODATA->>SAP: Consulta interna ABAP
    SAP-->>ODATA: Dados ABAP
    ODATA-->>APP: [{SalesOrder, SoldToParty, TotalNetAmount}]
    APP->>APP: Normaliza para modelo interno
    APP->>ODATA: POST /sap/opu/odata/sap/API_SALES_ORDER_SRV\n{SalesOrder, DeliveryStatus: "C"}
    ODATA-->>APP: HTTP 201 Created
```

### Endpoints OData Principais (SAP)

| Serviço OData | Entidade | Uso |
|---|---|---|
| `API_SALES_ORDER_SRV` | `A_SalesOrder` | Pedidos de venda |
| `API_CUSTOMER_SRV` | `A_Customer` | Cadastro de clientes |
| `API_MATERIAL_SRV` | `A_Product` | Produtos e materiais |
| `API_FINANCIAL_DOCUMENT_SRV` | `A_FinancialDocument` | Documentos financeiros |
| `API_PURCHASEORDER_PROCESS_SRV` | `A_PurchaseOrder` | Ordens de compra |

### Configuração (`.env`)

```env
# Credenciais SAP
SAP_URL_BASE=https://seu-servidor-sap
SAP_USUARIO=svc_integracao
SAP_SENHA=senha_segura
SAP_CLIENTE=100
SAP_MANDANTE=800
SAP_TIMEOUT_SEGUNDOS=60
SAP_VERSAO_ODATA=v4
```

---

## Oracle ERP Cloud

### Protocolo de Comunicação

Oracle ERP Cloud utiliza **REST API** com autenticação **Basic Auth** ou **OAuth 2.0 (IDCS)**.

```mermaid
sequenceDiagram
    participant APP as 🖥️ Nossa Aplicação
    participant OCI as 🔐 Oracle IDCS
    participant ORC as 🏢 Oracle ERP Cloud

    APP->>OCI: POST /oauth2/v1/token\n{grant_type: client_credentials}
    OCI-->>APP: {access_token, token_type: "Bearer"}
    APP->>ORC: GET /fscmRestApi/resources/11.13.18.05/orders\n?q=Status=BOOKED&limit=100
    ORC-->>APP: {items: [{OrderNumber, CustomerName, OrderedDate}]}
    APP->>APP: Processa pedidos novos
    APP->>ORC: PATCH /fscmRestApi/resources/.../orders/{OrderKey}\n{Status: "PICKED"}
    ORC-->>APP: HTTP 200 OK
```

### Endpoints REST Principais (Oracle)

| Recurso | Método | URL | Descrição |
|---|---|---|---|
| Pedidos | GET | `/fscmRestApi/resources/.../orders` | Lista pedidos |
| Clientes | GET | `/crmRestApi/resources/.../accounts` | Contas/clientes |
| Oportunidades | GET | `/crmRestApi/resources/.../opportunities` | Pipeline comercial |
| Faturas | GET | `/fscmRestApi/resources/.../invoices` | Faturas a receber |
| Fornecedores | GET | `/fscmRestApi/resources/.../suppliers` | Cadastro fornecedores |

### Configuração (`.env`)

```env
# Credenciais Oracle ERP Cloud
ORACLE_URL_BASE=https://seu-tenant.oraclecloud.com
ORACLE_CLIENTE_ID=seu_client_id
ORACLE_CLIENTE_SEGREDO=seu_client_secret
ORACLE_URL_IDCS=https://idcs-xxx.identity.oraclecloud.com
ORACLE_TIMEOUT_SEGUNDOS=45
```

---

## Mapeamento de Campos

### Pedido de Venda — Modelo Unificado

```mermaid
graph LR
    subgraph TOTVS_F["TOTVS"]
        T1[C5_NUM → número_pedido]
        T2[C5_CLIENTE → código_cliente]
        T3[C5_EMISSAO → data_criacao]
        T4[C5_VALBRUT → valor_total]
    end

    subgraph SAP_F["SAP"]
        S1[SalesOrder → número_pedido]
        S2[SoldToParty → código_cliente]
        S3[CreationDate → data_criacao]
        S4[TotalNetAmount → valor_total]
    end

    subgraph ORACLE_F["Oracle"]
        O1[OrderNumber → número_pedido]
        O2[CustomerName → código_cliente]
        O3[OrderedDate → data_criacao]
        O4[OrderedAmount → valor_total]
    end

    subgraph MODELO["Modelo Unificado"]
        M1[numero_pedido]
        M2[codigo_cliente]
        M3[data_criacao]
        M4[valor_total]
        M5[sistema_origem]
    end

    T1 --> M1
    T2 --> M2
    T3 --> M3
    T4 --> M4

    S1 --> M1
    S2 --> M2
    S3 --> M3
    S4 --> M4

    O1 --> M1
    O2 --> M2
    O3 --> M3
    O4 --> M4
```

### Tabela de Mapeamento Completa

| Campo Unificado | TOTVS | SAP OData | Oracle REST | Tipo |
|---|---|---|---|---|
| `numero_pedido` | `C5_NUM` | `SalesOrder` | `OrderNumber` | `str` |
| `codigo_cliente` | `C5_CLIENTE` | `SoldToParty` | `CustomerAccountNumber` | `str` |
| `nome_cliente` | `A1_NOME` | `SoldToPartyName` | `CustomerName` | `str` |
| `data_criacao` | `C5_EMISSAO` | `CreationDate` | `OrderedDate` | `date` |
| `data_entrega` | `C5_ENTREG` | `RequestedDeliveryDate` | `RequestedShipDate` | `date` |
| `valor_total` | `C5_VALBRUT` | `TotalNetAmount` | `OrderedAmount` | `decimal` |
| `moeda` | `C5_MOEDA` | `TransactionCurrency` | `TransactionCurrencyCode` | `str` |
| `status_pedido` | `C5_STATUS` | `OverallDeliveryStatus` | `StatusCode` | `str` |
| `sistema_origem` | `"TOTVS"` | `"SAP"` | `"ORACLE"` | `str` |

---

## Tratamento de Erros

```mermaid
flowchart TD
    INICIO([Início da Integração]) --> CONECTA{Conecta ao ERP?}
    CONECTA -->|Não| ERRO_CON[Erro de Conexão]
    CONECTA -->|Sim| AUTENTICA{Autentica?}
    AUTENTICA -->|Não| ERRO_AUTH[Erro de Autenticação]
    AUTENTICA -->|Sim| BUSCA[Busca Dados]
    BUSCA --> VALIDA{Dados válidos?}
    VALIDA -->|Não| ERRO_VAL[Erro de Validação]
    VALIDA -->|Sim| TRANSFORMA[Transforma para modelo unificado]
    TRANSFORMA --> PERSISTE{Persiste com sucesso?}
    PERSISTE -->|Não| ERRO_DB[Erro de Banco de Dados]
    PERSISTE -->|Sim| SUCESSO([✅ Integração Concluída])

    ERRO_CON --> RETRY{Tentativas < 3?}
    ERRO_AUTH --> LOG_AUTH[Registra log de erro]
    ERRO_VAL --> DLQ[Dead Letter Queue]
    ERRO_DB --> RETRY

    RETRY -->|Sim| CONECTA
    RETRY -->|Não| ALERTA[Envia alerta ao time]
    LOG_AUTH --> ALERTA
    DLQ --> ALERTA
    ALERTA --> FIM([Fim com Erro])

    style SUCESSO fill:#c8e6c9,stroke:#388E3C
    style FIM fill:#ffcdd2,stroke:#D32F2F
    style ERRO_CON fill:#fff9c4
    style ERRO_AUTH fill:#fff9c4
    style ERRO_VAL fill:#fff9c4
    style ERRO_DB fill:#fff9c4
```

### Códigos de Erro Padronizados

| Código | Descrição | Ação |
|---|---|---|
| `INT-001` | Timeout de conexão | Retry automático (3x) |
| `INT-002` | Token expirado | Renovação automática |
| `INT-003` | Dados inválidos | Envio para DLQ + alerta |
| `INT-004` | Limite de requisições (rate limit) | Backoff exponencial |
| `INT-005` | Serviço indisponível | Alerta + circuit breaker |
| `INT-006` | Erro de mapeamento de campo | Log detalhado + DLQ |

---

## Exemplos de Payload

### Entrada — Pedido TOTVS (raw)

```json
{
  "C5_NUM": "000123",
  "C5_CLIENTE": "CLI001",
  "A1_NOME": "Empresa ABC Ltda",
  "C5_EMISSAO": "20260508",
  "C5_ENTREG": "20260515",
  "C5_VALBRUT": 15000.00,
  "C5_MOEDA": "BRL",
  "C5_STATUS": "L",
  "itens": [
    {"C6_PRODUTO": "PROD001", "C6_QTDVEN": 10, "C6_PRCVEN": 1500.00}
  ]
}
```

### Saída — Modelo Unificado (normalizado)

```json
{
  "numero_pedido": "000123",
  "codigo_cliente": "CLI001",
  "nome_cliente": "Empresa ABC Ltda",
  "data_criacao": "2026-05-08",
  "data_entrega": "2026-05-15",
  "valor_total": 15000.00,
  "moeda": "BRL",
  "status_pedido": "LIBERADO",
  "sistema_origem": "TOTVS",
  "data_processamento": "2026-05-08T03:57:57Z",
  "itens": [
    {
      "codigo_produto": "PROD001",
      "quantidade": 10,
      "preco_unitario": 1500.00,
      "valor_item": 15000.00
    }
  ]
}
```
