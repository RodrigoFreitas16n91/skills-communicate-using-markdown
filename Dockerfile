# ============================================================
# Dockerfile — Plataforma de Integrações ERP/CRM
# Descrição: Imagem Docker multi-stage para a plataforma.
#            Estágio "base" instala dependências.
#            Estágio "desenvolvimento" adiciona ferramentas dev.
#            Estágio "producao" gera imagem mínima e segura.
# Autor: Rodrigo Freitas
# ============================================================

# -------------------------------------------------------
# ESTÁGIO 1: base — instala dependências do sistema
# -------------------------------------------------------
FROM python:3.12-slim AS base

# Define variáveis de ambiente para evitar prompts interativos
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Diretório de trabalho da aplicação
WORKDIR /app

# Instala dependências do sistema operacional necessárias
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Necessário para compilar algumas bibliotecas Python
    gcc \
    libpq-dev \
    # Curl para health checks
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas os arquivos de dependências primeiro (cache do Docker)
COPY requirements.txt requirements-dev.txt ./

# -------------------------------------------------------
# ESTÁGIO 2: desenvolvimento — ferramentas extras para dev
# -------------------------------------------------------
FROM base AS desenvolvimento

# Instala todas as dependências (incluindo as de desenvolvimento)
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Copia o código-fonte completo
COPY . .

# Porta da API em desenvolvimento
EXPOSE 8000

# Comando padrão em desenvolvimento (com reload automático)
CMD ["uvicorn", "mcp.servidor:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# -------------------------------------------------------
# ESTÁGIO 3: producao — imagem mínima e segura
# -------------------------------------------------------
FROM base AS producao

# Instala somente dependências de produção
RUN pip install --no-cache-dir -r requirements.txt

# Cria usuário não-root para execução segura (boa prática de segurança)
RUN groupadd --gid 1001 appgrupo && \
    useradd --uid 1001 --gid appgrupo --no-create-home --shell /bin/false appusuario

# Copia o código-fonte da aplicação
COPY --chown=appusuario:appgrupo . .

# Remove arquivos desnecessários em produção
RUN rm -rf testes/ docs/ *.md .env* .git*

# Alterna para o usuário não-root
USER appusuario

# Porta da API em produção
EXPOSE 8000

# Health check interno do container
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/saude || exit 1

# Comando de inicialização em produção (sem reload)
CMD ["uvicorn", "mcp.servidor:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
