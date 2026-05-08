# 🚀 CI/CD e DevOps com GitHub Actions

> **Versão:** 1.0.0 · **Módulo:** Integração e Entrega Contínua  
> **Ferramentas:** GitHub Actions, Docker, Docker Hub / GHCR

---

## 📋 Sumário

1. [Visão Geral do Pipeline](#visão-geral-do-pipeline)
2. [Ambientes e Estratégia de Deploy](#ambientes-e-estratégia-de-deploy)
3. [Pipeline CI — Integração Contínua](#pipeline-ci--integração-contínua)
4. [Pipeline CD — Entrega Contínua](#pipeline-cd--entrega-contínua)
5. [Gestão de Secrets e Variáveis](#gestão-de-secrets-e-variáveis)
6. [Rollback e Recuperação](#rollback-e-recuperação)
7. [Qualidade de Código](#qualidade-de-código)

---

## Visão Geral do Pipeline

```mermaid
flowchart LR
    subgraph DEV_FLOW["👨‍💻 Dev"]
        COMMIT[git commit\ngit push]
        PR[Pull Request\naberto]
    end

    subgraph CI_PIPE["⚙️ CI - Integração Contínua"]
        LINT_CI[1. Lint\n& Formatação]
        TEST_CI[2. Testes\nUnitários]
        TEST_INT[3. Testes de\nIntegração]
        SEC_SCAN[4. Scan de\nSegurança]
        BUILD_IMG[5. Build\nImagem Docker]
    end

    subgraph CD_STAGING["🧪 CD - Staging"]
        PUSH_STG[Push imagem\npara registry]
        DEPLOY_STG[Deploy em\nStaging]
        SMOKE_STG[Smoke Tests\nStaging]
    end

    subgraph APROVACAO["✋ Aprovação"]
        REVIEW[Code Review\n(1 aprovação)]
        QA_OK[QA Aprovado\nno Staging]
    end

    subgraph CD_PROD["🚀 CD - Produção"]
        TAG_RELEASE[Cria tag\nde release]
        DEPLOY_PROD[Deploy em\nProdução]
        HEALTH[Health Check\nPós-deploy]
        NOTIF[Notifica\ntime no Slack]
    end

    COMMIT --> PR
    PR --> LINT_CI --> TEST_CI --> TEST_INT --> SEC_SCAN --> BUILD_IMG
    BUILD_IMG --> PUSH_STG --> DEPLOY_STG --> SMOKE_STG
    SMOKE_STG --> REVIEW
    REVIEW --> QA_OK --> TAG_RELEASE --> DEPLOY_PROD --> HEALTH --> NOTIF

    style CI_PIPE fill:#e3f2fd
    style CD_STAGING fill:#fff8e1
    style APROVACAO fill:#f3e5f5
    style CD_PROD fill:#e8f5e9
```

---

## Ambientes e Estratégia de Deploy

```mermaid
graph TB
    subgraph GIT["📂 Repositório Git"]
        BRANCH_F[feature/*]
        BRANCH_S[staging]
        BRANCH_M[main]
    end

    subgraph ENVS["🌍 Ambientes"]
        ENV_DEV[Desenvolvimento\nlocal]
        ENV_STG[Staging\nhomologacao]
        ENV_PROD[Produção\nprod]
    end

    subgraph REGISTRIES["🐳 Container Registry"]
        IMG_STG[imagem:staging-abc123]
        IMG_PROD[imagem:v1.2.3]
    end

    BRANCH_F -->|PR → staging| BRANCH_S
    BRANCH_S -->|CI verde + review| BRANCH_M

    BRANCH_F -.->|docker-compose local| ENV_DEV
    BRANCH_S -->|deploy automático| ENV_STG
    BRANCH_M -->|deploy manual aprovado| ENV_PROD

    ENV_STG -.->|usa| IMG_STG
    ENV_PROD -.->|usa| IMG_PROD

    style ENV_DEV fill:#e3f2fd
    style ENV_STG fill:#fff8e1
    style ENV_PROD fill:#e8f5e9
```

### Matriz de Deploy por Ambiente

| Ambiente | Branch | Trigger | Aprovação necessária | URL |
|---|---|---|---|---|
| Desenvolvimento | `feature/*` | Manual (local) | Nenhuma | `localhost:8000` |
| Staging | `staging` | Automático (push) | CI verde | `staging.empresa.com` |
| Produção | `main` | Manual (workflow_dispatch) | 1 aprovador | `api.empresa.com` |

---

## Pipeline CI — Integração Contínua

### Fluxo Detalhado do CI

```mermaid
sequenceDiagram
    participant DEV3 as 👨‍💻 Dev
    participant GH2 as 🐙 GitHub
    participant RUNNER as ⚙️ GitHub Runner
    participant REGISTRY as 🐳 Container Registry
    participant SLACK4 as 💬 Slack

    DEV3->>GH2: git push feature/minha-feature
    GH2->>RUNNER: Dispara workflow ci.yml
    RUNNER->>RUNNER: Checkout do código
    RUNNER->>RUNNER: Setup Python 3.12
    RUNNER->>RUNNER: pip install dependências
    RUNNER->>RUNNER: flake8 (lint)
    RUNNER->>RUNNER: black --check (formatação)
    RUNNER->>RUNNER: pytest (testes unitários)
    RUNNER->>RUNNER: pytest --integration (testes integração)
    RUNNER->>RUNNER: bandit (scan segurança)
    RUNNER->>RUNNER: trivy (scan imagem Docker)
    RUNNER->>RUNNER: docker build
    RUNNER->>REGISTRY: docker push imagem:pr-42
    RUNNER-->>GH2: ✅ CI Passou / ❌ CI Falhou
    GH2-->>DEV3: Notificação de status
    GH2->>SLACK4: Notificação no canal #ci-cd
```

---

## Pipeline CD — Entrega Contínua

### Deploy em Staging (automático)

```mermaid
flowchart TD
    MERGE_STG([Merge em staging]) --> BUILD_STG[Build imagem Docker\ntag: staging-SHA_COMMIT]
    BUILD_STG --> PUSH_REGISTRY[Push para Container\nRegistry]
    PUSH_REGISTRY --> DEPLOY_DOCKER[docker-compose pull\ndocker-compose up -d]
    DEPLOY_DOCKER --> AGUARDA[Aguarda 30s\nserviços subirem]
    AGUARDA --> HEALTH_STG{Health check\npassou?}
    HEALTH_STG -->|Sim| SMOKE[Executa smoke tests\nautomáticos]
    HEALTH_STG -->|Não| ROLLBACK_STG[Rollback automático\npara versão anterior]
    SMOKE --> NOTIF_STG[Notifica time:\n✅ Staging OK]
    ROLLBACK_STG --> ALERTA_STG[Alerta:\n❌ Deploy falhou]

    style NOTIF_STG fill:#c8e6c9
    style ALERTA_STG fill:#ffcdd2
```

### Deploy em Produção (aprovação manual)

```mermaid
flowchart TD
    TRIGGER([workflow_dispatch\nou tag v*]) --> VALIDA{Branch é main\ne CI verde?}
    VALIDA -->|Não| BLOQUEIA[Bloqueia deploy\n❌]
    VALIDA -->|Sim| APROVACAO2{Aguarda aprovação\ndo responsável}
    APROVACAO2 -->|Aprovado| TAG_V[Cria tag Git\nv1.2.3]
    APROVACAO2 -->|Negado| CANCELA[Cancela deploy]
    TAG_V --> BUILD_PROD[Build imagem\ntag: v1.2.3]
    BUILD_PROD --> BLUE_GREEN{Estratégia\nBlue/Green}
    BLUE_GREEN --> NOVO_ENV[Sobe ambiente GREEN\nnova versão]
    NOVO_ENV --> HEALTH_PROD{Health check\nGREEN OK?}
    HEALTH_PROD -->|Sim| SWITCH[Switch tráfego\nBLUE → GREEN]
    HEALTH_PROD -->|Não| ROLLBACK_PROD[Mantém BLUE\ndestrói GREEN]
    SWITCH --> MONITOR_10[Monitora 10 minutos]
    MONITOR_10 --> DESTROI_BLUE[Destroi ambiente BLUE\nantigo]
    DESTROI_BLUE --> NOTIF_PROD[Notifica:\n🚀 Deploy v1.2.3 em Produção!]

    style NOTIF_PROD fill:#c8e6c9,stroke:#388E3C
    style ROLLBACK_PROD fill:#ffcdd2
    style BLOQUEIA fill:#ffcdd2
```

---

## Gestão de Secrets e Variáveis

### Organização dos Secrets no GitHub

```
Repositório GitHub
├── Settings
│   └── Secrets and variables
│       ├── Actions secrets (criptografados)
│       │   ├── POSTGRES_SENHA           # Senha do banco
│       │   ├── REDIS_SENHA              # Senha do Redis
│       │   ├── TOTVS_SENHA              # Credencial TOTVS
│       │   ├── SAP_SENHA                # Credencial SAP
│       │   ├── ORACLE_CLIENTE_SEGREDO   # Segredo OAuth Oracle
│       │   ├── DOCKER_REGISTRY_SENHA    # Senha do registry
│       │   ├── SLACK_WEBHOOK_URL        # Webhook para notificações
│       │   └── LLM_CHAVE_API            # Chave da API do LLM
│       └── Actions variables (não criptografados)
│           ├── AMBIENTE_STAGING=homologacao
│           ├── AMBIENTE_PROD=producao
│           ├── DOCKER_REGISTRY=ghcr.io/org/projeto
│           └── SLACK_CANAL_ALERTAS=#ci-cd
```

### Hierarquia de Prioridade de Variáveis

```
1. Secrets do GitHub Actions (maior prioridade)
2. Variáveis de ambiente do ambiente (staging/prod)
3. Arquivo .env.{ambiente} (não commitado)
4. Arquivo .env.default (valores padrão, commitado)
```

---

## Rollback e Recuperação

```mermaid
flowchart LR
    PROBLEMA([Problema\ndetectado]) --> DECISAO{Tipo de\nproblema}

    DECISAO -->|Bug crítico em prod| ROLLBACK_AUTO[Rollback automático\npara versão anterior]
    DECISAO -->|Degradação de performance| SCALE_UP[Escalar horizontalmente\ndocker-compose scale]
    DECISAO -->|Falha de dependência| CIRCUIT_B[Circuit Breaker\nativa]

    ROLLBACK_AUTO --> IMAGEM_ANTERIOR[docker pull imagem:v1.2.2\ndocker-compose up -d]
    SCALE_UP --> MAIS_WORKERS[Aumenta workers\nde 2 para 4]
    CIRCUIT_B --> MODO_DEG[Modo degradado\nrespostas em cache]

    IMAGEM_ANTERIOR --> VERIFICA[Verifica saúde\ndo sistema]
    MAIS_WORKERS --> VERIFICA
    MODO_DEG --> VERIFICA

    VERIFICA --> NOTIF_ROLLBACK[Notifica time\ndo rollback]
    NOTIF_ROLLBACK --> POST_MORTEM[Abre card\nno Trello\npara análise]

    style ROLLBACK_AUTO fill:#fff9c4
    style POST_MORTEM fill:#e3f2fd
```

### Histórico de Versões para Rollback

| Imagem | Versão | Ambiente | Data | Status |
|---|---|---|---|---|
| `projeto:v1.3.0` | Atual | Produção | 2026-05-08 | 🟢 Ativo |
| `projeto:v1.2.3` | Anterior | Arquivado | 2026-04-20 | 🟡 Disponível |
| `projeto:v1.2.0` | Legado | Arquivado | 2026-03-15 | 🟡 Disponível |
| `projeto:v1.1.0` | Muito antigo | Removido | 2026-02-01 | 🔴 Indisponível |

> **Política de retenção:** últimas 3 versões de produção mantidas no registry

---

## Qualidade de Código

### Ferramentas de Qualidade Integradas ao CI

```mermaid
graph TB
    subgraph ESTATICA["🔍 Análise Estática"]
        FLAKE8[flake8\nPEP8 + erros]
        PYLINT[pylint\nQualidade geral]
        MYPY[mypy\nTipagem estática]
        BLACK[black\nFormatação]
    end

    subgraph SEGURANCA_Q["🔐 Segurança"]
        BANDIT[bandit\nVulnerabilidades Python]
        TRIVY2[trivy\nVulnerabilidades Docker]
        DEPENDABOT[Dependabot\nDependências desatualizadas]
    end

    subgraph TESTES_Q["🧪 Testes"]
        PYTEST[pytest\nTestes unitários]
        COVERAGE[coverage.py\nCobertura ≥ 80%]
        PYTEST_INT[pytest -m integration\nTestes de integração]
    end

    subgraph GATE["🚦 Quality Gate"]
        GATE_OK{Todos os\nchecks verdes?}
        APROVADO([✅ PR liberado\npara merge])
        BLOQUEADO([❌ PR bloqueado])
    end

    FLAKE8 --> GATE_OK
    PYLINT --> GATE_OK
    MYPY --> GATE_OK
    BLACK --> GATE_OK
    BANDIT --> GATE_OK
    TRIVY2 --> GATE_OK
    PYTEST --> GATE_OK
    COVERAGE --> GATE_OK
    PYTEST_INT --> GATE_OK

    GATE_OK -->|Sim| APROVADO
    GATE_OK -->|Não| BLOQUEADO

    style APROVADO fill:#c8e6c9,stroke:#388E3C
    style BLOQUEADO fill:#ffcdd2,stroke:#D32F2F
```

### Thresholds de Qualidade

| Métrica | Threshold mínimo | Bloqueia PR? |
|---|---|---|
| Cobertura de testes | ≥ 80% | ✅ Sim |
| Score pylint | ≥ 8.0/10 | ✅ Sim |
| Vulnerabilidades críticas (bandit) | 0 | ✅ Sim |
| CVEs críticos (trivy) | 0 | ✅ Sim |
| Erros de formatação (black) | 0 | ✅ Sim |
| Erros de tipo (mypy) | 0 | ✅ Sim |
| Avisos pylint | Sem limite | ❌ Não |
