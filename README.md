
<div align="center">

# 🏗️ Plataforma de Integrações ERP/CRM com MCP e Docker

[![CI/CD](https://github.com/RodrigoFreitas16n91/skills-communicate-using-markdown/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/RodrigoFreitas16n91/skills-communicate-using-markdown/actions/workflows/ci-cd.yml)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](docker-compose.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**Sistema de integração inteligente entre ERPs (TOTVS, SAP, Oracle) e CRMs com uso de MCP, Docker, Agentes de IA e pipelines CI/CD.**

</div>

---

## 📋 Índice de Documentação Técnica

| Documento | Descrição |
|---|---|
| [🏗️ Arquitetura Geral](docs/ARQUITETURA.md) | Visão geral, diagramas de componentes e tecnologias |
| [🔌 Integrações ERP/CRM](docs/INTEGRACAO_ERP_CRM.md) | TOTVS, SAP, Oracle — protocolos, mapeamentos e exemplos |
| [📊 Governança de T.I.](docs/GOVERNANCA_TI.md) | Políticas, SLAs, RBAC, incidentes e boas práticas |
| [🤖 Agentes Inteligentes](docs/AGENTES_AUTOMATIZACAO.md) | Catálogo de agentes, automações e protocolo MCP |
| [📋 Metodologia Ágil](docs/METODOLOGIA_AGIL.md) | Scrum, Trello, fluxo de desenvolvimento e DoD |
| [🚀 CI/CD e DevOps](docs/CICD_DEVOPS.md) | GitHub Actions, pipelines de deploy, qualidade |

---

## 🚀 Início Rápido

### Pré-requisitos

- Docker 26+ e Docker Compose 2+
- Python 3.12+ (para desenvolvimento local)
- Git

### Subindo o ambiente completo

```bash
# 1. Clone o repositório
git clone https://github.com/RodrigoFreitas16n91/skills-communicate-using-markdown.git
cd skills-communicate-using-markdown

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas credenciais reais

# 3. Sobe todos os serviços
docker-compose up -d

# 4. Verifica se os serviços estão saudáveis
docker-compose ps
```

### Serviços disponíveis após o `docker-compose up`

| Serviço | URL | Descrição |
|---|---|---|
| API Principal (MCP) | http://localhost:8000 | Servidor MCP + API REST |
| Agentes | http://localhost:8002 | Status dos agentes inteligentes |
| RabbitMQ (Painel) | http://localhost:15672 | Gerenciamento de filas |
| Kibana (Logs) | http://localhost:5601 | Painel de logs |
| Grafana (Métricas) | http://localhost:3000 | Dashboards de monitoramento |

---

## 🏛️ Arquitetura Resumida

```
┌─────────────────────────────────────────────────────┐
│               PLATAFORMA DE INTEGRAÇÕES              │
│                                                     │
│   TOTVS ──┐                                         │
│   SAP   ──┼──► API Gateway ──► MCP Orquestrador     │
│   Oracle ─┘         │               │               │
│                      │         ┌────▼─────┐         │
│                      │         │ Agentes  │         │
│                      │         │   de IA  │         │
│                      │         └────┬─────┘         │
│                      │              │               │
│                   PostgreSQL ◄──────┘               │
│                   Redis Cache                       │
│                   RabbitMQ Filas                    │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Projeto

```
.
├── agentes/                    # Agentes inteligentes de integração
│   └── agente_integracao.py   # Agente principal de sincronização
├── conectores/                 # Conectores para cada ERP/CRM
│   └── conector_totvs.py      # Conector TOTVS Protheus
├── docs/                       # Documentação técnica completa
│   ├── ARQUITETURA.md         # Arquitetura e diagramas
│   ├── INTEGRACAO_ERP_CRM.md  # Guia de integrações
│   ├── GOVERNANCA_TI.md       # Governança e compliance
│   ├── AGENTES_AUTOMATIZACAO.md # Agentes e automações
│   ├── METODOLOGIA_AGIL.md    # Metodologia ágil
│   └── CICD_DEVOPS.md         # CI/CD e DevOps
├── mcp/                        # Configurações do servidor MCP
│   └── servidor-mcp-config.json
├── .github/
│   └── workflows/
│       └── ci-cd.yml          # Pipeline GitHub Actions
├── docker-compose.yml          # Orquestração dos serviços
├── Dockerfile                  # Imagem Docker multi-stage
├── .env.example               # Modelo de variáveis de ambiente
└── README.md                  # Este arquivo
```

---

## 🛡️ Segurança

- ✅ Autenticação via OAuth2 + JWT
- ✅ Secrets gerenciados via variáveis de ambiente / Docker Secrets
- ✅ Scan automático de vulnerabilidades (Bandit + Trivy) no CI
- ✅ Usuário não-root nos containers Docker
- ✅ TLS em todas as comunicações (produção)
- ✅ Conformidade com LGPD (pseudonimização de dados pessoais)

---

## 🤝 Contribuindo

1. Leia a [Metodologia Ágil](docs/METODOLOGIA_AGIL.md) para entender o fluxo de trabalho
2. Crie uma branch `feature/us-XXX-descricao` a partir de `staging`
3. Siga as convenções de commit (Conventional Commits em pt-br)
4. Abra um Pull Request com evidências de testes

---

<div align="center">

*Construído com ❤️ por Rodrigo Freitas*

</div>

---

<!-- Seção original do GitHub Skills -->
<div align="center">

# 🎉 Congratulations RodrigoFreitas16n91! 🎉

<img src="https://octodex.github.com/images/welcometocat.png" height="200px" />

### 🌟 You've successfully completed the exercise! 🌟

## 🚀 Share Your Success!

**Show off your new skills and inspire others!**

<a href="https://twitter.com/intent/tweet?text=I%20just%20completed%20the%20%22Communicate%20using%20Markdown%22%20GitHub%20Skills%20hands-on%20exercise!%20%F0%9F%8E%89%0A%0Ahttps%3A%2F%2Fgithub.com%2FRodrigoFreitas16n91%2Fskills-communicate-using-markdown%0A%0A%23GitHubSkills%20%23OpenSource%20%23GitHubLearn%0A" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/Share%20on%20X-1da1f2?style=for-the-badge&logo=x&logoColor=white" alt="Share on X" />
</a>
<a href="https://bsky.app/intent/compose?text=I%20just%20completed%20the%20%22Communicate%20using%20Markdown%22%20GitHub%20Skills%20hands-on%20exercise!%20%F0%9F%8E%89%0A%0Ahttps%3A%2F%2Fgithub.com%2FRodrigoFreitas16n91%2Fskills-communicate-using-markdown%0A%0A%23GitHubSkills%20%23OpenSource%20%23GitHubLearn%0A" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/Share%20on%20Bluesky-0085ff?style=for-the-badge&logo=bluesky&logoColor=white" alt="Share on Bluesky" />
</a>
<a href="https://www.linkedin.com/feed/?shareActive=true&text=I%20just%20completed%20the%20%22Communicate%20using%20Markdown%22%20GitHub%20Skills%20hands-on%20exercise!%20%F0%9F%8E%89%0A%0Ahttps%3A%2F%2Fgithub.com%2FRodrigoFreitas16n91%2Fskills-communicate-using-markdown%0A%0A%23GitHubSkills%20%23OpenSource%20%23GitHubLearn%0A" target="_blank" rel="noopener noreferrer">
  <img src="https://img.shields.io/badge/Share%20on%20LinkedIn-0077b5?style=for-the-badge&logo=linkedin&logoColor=white" alt="Share on LinkedIn" />
</a>

### 🎯 What's Next?
**Keep the momentum going!**

[![](https://img.shields.io/badge/Return%20to%20Exercise-%E2%86%92-1f883d?style=for-the-badge&logo=github&labelColor=197935)](https://github.com/RodrigoFreitas16n91/skills-communicate-using-markdown/issues/1)
[![GitHub Skills](https://img.shields.io/badge/Explore%20GitHub%20Skills-000000?style=for-the-badge&logo=github&logoColor=white)](https://skills.github.com)

*There's no better way to learn than building things!* 🚀

</div>

---

&copy; 2025 GitHub &bull; [Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md) &bull; [MIT License](https://gh.io/mit)

