"""
Conector TOTVS Protheus — Plataforma de Integrações
====================================================
Descrição:
    Conector responsável por toda a comunicação com o
    sistema ERP TOTVS Protheus via REST API ou Web Services.

    Funcionalidades:
    - Autenticação OAuth2 com renovação automática de token
    - Busca de pedidos, clientes, produtos e estoque
    - Envio de confirmações e atualizações de status
    - Retry automático com backoff exponencial em falhas

Autor: Rodrigo Freitas
Versão: 1.0.0
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

# Logger específico deste módulo
logger = logging.getLogger(__name__)

# Tempo mínimo em segundos antes de renovar o token (margem de segurança)
MARGEM_RENOVACAO_TOKEN_SEGUNDOS = 60

# Quantidade máxima de tentativas em caso de falha transitória
MAXIMO_TENTATIVAS = 3

# Tempo base de espera entre tentativas (em segundos)
ESPERA_BASE_RETRY_SEGUNDOS = 2


class ErroAutenticacaoTOTVS(Exception):
    """Exceção lançada quando a autenticação com o TOTVS falha."""


class ErroConexaoTOTVS(Exception):
    """Exceção lançada quando não é possível conectar ao TOTVS."""


class ConectorTOTVS:
    """
    Conector para integração com o TOTVS Protheus via REST API.

    Gerencia autenticação, cache de token e comunicação HTTP
    com o servidor TOTVS, incluindo retry automático.

    Exemplo de uso:
        conector = ConectorTOTVS(
            url_base="https://totvs.empresa.com:8080",
            usuario="usuario_integracao",
            senha="senha_segura",
            empresa="01",
            filial="0101",
        )
        pedidos = conector.buscar_pedidos(data_inicio=datetime(2026, 5, 1))
    """

    def __init__(
        self,
        url_base: str,
        usuario: str,
        senha: str,
        empresa: str,
        filial: str,
        timeout_segundos: int = 30,
    ) -> None:
        """
        Inicializa o conector TOTVS.

        Args:
            url_base: URL base do servidor TOTVS (ex: https://totvs.empresa.com:8080).
            usuario: Usuário de integração cadastrado no TOTVS.
            senha: Senha do usuário de integração.
            empresa: Código da empresa no TOTVS (ex: "01").
            filial: Código da filial no TOTVS (ex: "0101").
            timeout_segundos: Timeout das requisições HTTP em segundos.
        """
        self.url_base = url_base.rstrip("/")
        self.usuario = usuario
        self.senha = senha
        self.empresa = empresa
        self.filial = filial
        self.timeout_segundos = timeout_segundos

        # Controle interno do token de acesso
        self._token_acesso: str | None = None
        self._token_expira_em: datetime | None = None

        logger.info(
            "ConectorTOTVS inicializado. Servidor: %s | Empresa: %s | Filial: %s",
            self.url_base,
            self.empresa,
            self.filial,
        )

    # ----------------------------------------------------------
    # AUTENTICAÇÃO
    # ----------------------------------------------------------

    def _token_esta_valido(self) -> bool:
        """
        Verifica se o token atual ainda é válido.

        Retorna False se o token estiver próximo do vencimento
        (dentro da margem de segurança configurada).
        """
        if not self._token_acesso or not self._token_expira_em:
            return False

        margem = timedelta(seconds=MARGEM_RENOVACAO_TOKEN_SEGUNDOS)
        return datetime.now(timezone.utc) < (self._token_expira_em - margem)

    def autenticar(self) -> None:
        """
        Realiza autenticação OAuth2 no servidor TOTVS e
        armazena o token para uso nas requisições subsequentes.

        Raises:
            ErroAutenticacaoTOTVS: Se as credenciais forem rejeitadas.
            ErroConexaoTOTVS: Se não for possível alcançar o servidor.
        """
        url_autenticacao = f"{self.url_base}/oauth/token"
        corpo_requisicao = {
            "grant_type": "password",
            "username": self.usuario,
            "password": self.senha,
        }

        logger.debug("Autenticando no TOTVS em: %s", url_autenticacao)

        try:
            with httpx.Client(timeout=self.timeout_segundos) as cliente:
                resposta = cliente.post(url_autenticacao, json=corpo_requisicao)
                resposta.raise_for_status()
                dados_token = resposta.json()

        except httpx.ConnectError as excecao:
            mensagem = f"Não foi possível conectar ao TOTVS em {self.url_base}: {excecao}"
            logger.error(mensagem)
            raise ErroConexaoTOTVS(mensagem) from excecao

        except httpx.HTTPStatusError as excecao:
            if excecao.response.status_code in (401, 403):
                mensagem = f"Credenciais inválidas para o TOTVS. Usuário: {self.usuario}"
                logger.error(mensagem)
                raise ErroAutenticacaoTOTVS(mensagem) from excecao
            raise

        # Salva token e calcula expiração
        self._token_acesso = dados_token["access_token"]
        segundos_expiracao = dados_token.get("expires_in", 3600)
        self._token_expira_em = datetime.now(timezone.utc) + timedelta(seconds=segundos_expiracao)

        logger.info(
            "Autenticação TOTVS bem-sucedida. Token expira em: %s",
            self._token_expira_em.isoformat(),
        )

    def _obter_cabecalhos(self) -> dict[str, str]:
        """
        Retorna os cabeçalhos HTTP para as requisições ao TOTVS,
        renovando o token se necessário.

        Returns:
            Dicionário com os cabeçalhos Authorization, empresa e filial.
        """
        if not self._token_esta_valido():
            logger.debug("Token expirado ou ausente. Renovando...")
            self.autenticar()

        return {
            "Authorization": f"Bearer {self._token_acesso}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Empresa": self.empresa,
            "X-Filial": self.filial,
        }

    # ----------------------------------------------------------
    # REQUISIÇÕES COM RETRY
    # ----------------------------------------------------------

    def _fazer_requisicao(
        self,
        metodo: str,
        endpoint: str,
        parametros: dict[str, Any] | None = None,
        corpo: dict[str, Any] | None = None,
    ) -> Any:
        """
        Executa uma requisição HTTP com retry automático e
        backoff exponencial em caso de falhas transitórias.

        Args:
            metodo: Método HTTP ("GET", "POST", "PUT", "PATCH").
            endpoint: Caminho do endpoint (ex: "/api/pedidos").
            parametros: Parâmetros de query string (opcional).
            corpo: Corpo da requisição JSON (opcional).

        Returns:
            Resposta desserializada do JSON.

        Raises:
            ErroConexaoTOTVS: Após esgotar todas as tentativas de retry.
        """
        url_completa = f"{self.url_base}{endpoint}"

        for numero_tentativa in range(1, MAXIMO_TENTATIVAS + 1):
            try:
                cabecalhos = self._obter_cabecalhos()

                with httpx.Client(timeout=self.timeout_segundos) as cliente:
                    resposta = cliente.request(
                        method=metodo,
                        url=url_completa,
                        headers=cabecalhos,
                        params=parametros,
                        json=corpo,
                    )
                    resposta.raise_for_status()
                    return resposta.json()

            except httpx.TimeoutException:
                tempo_espera = ESPERA_BASE_RETRY_SEGUNDOS ** numero_tentativa
                logger.warning(
                    "Timeout na tentativa %d/%d para %s. Aguardando %ds...",
                    numero_tentativa,
                    MAXIMO_TENTATIVAS,
                    url_completa,
                    tempo_espera,
                )
                if numero_tentativa < MAXIMO_TENTATIVAS:
                    time.sleep(tempo_espera)

            except httpx.HTTPStatusError as excecao:
                # Erros 4xx não devem ser retentados (erro do cliente)
                if 400 <= excecao.response.status_code < 500:
                    logger.error(
                        "Erro %d na requisição ao TOTVS: %s",
                        excecao.response.status_code,
                        excecao.response.text,
                    )
                    raise

                # Erros 5xx são transitórios — faz retry
                tempo_espera = ESPERA_BASE_RETRY_SEGUNDOS ** numero_tentativa
                logger.warning(
                    "Erro %d transitório (tentativa %d/%d). Aguardando %ds...",
                    excecao.response.status_code,
                    numero_tentativa,
                    MAXIMO_TENTATIVAS,
                    tempo_espera,
                )
                if numero_tentativa < MAXIMO_TENTATIVAS:
                    time.sleep(tempo_espera)

        raise ErroConexaoTOTVS(
            f"Esgotadas {MAXIMO_TENTATIVAS} tentativas para {url_completa}."
        )

    # ----------------------------------------------------------
    # MÉTODOS DE NEGÓCIO
    # ----------------------------------------------------------

    def buscar_pedidos(
        self,
        data_inicio: datetime,
        data_fim: datetime | None = None,
        tamanho_pagina: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Busca pedidos de venda no TOTVS dentro do período informado.

        Args:
            data_inicio: Data inicial do filtro (obrigatória).
            data_fim: Data final do filtro (padrão: hoje).
            tamanho_pagina: Quantidade de registros por página.

        Returns:
            Lista de pedidos no formato raw do TOTVS.
        """
        data_fim = data_fim or datetime.now(timezone.utc)

        # Formata datas no padrão TOTVS: YYYYMMDD
        data_inicio_str = data_inicio.strftime("%Y%m%d")
        data_fim_str = data_fim.strftime("%Y%m%d")

        parametros_busca = {
            "dtini": data_inicio_str,
            "dtfim": data_fim_str,
            "pagesize": tamanho_pagina,
            "page": 1,
        }

        todos_pedidos: list[dict[str, Any]] = []
        pagina_atual = 1

        while True:
            parametros_busca["page"] = pagina_atual
            logger.debug(
                "Buscando pedidos TOTVS — página %d (de %s a %s)",
                pagina_atual,
                data_inicio_str,
                data_fim_str,
            )

            resposta_pagina = self._fazer_requisicao("GET", "/api/pedidos", parametros=parametros_busca)

            # Suporte a resposta paginada ou lista simples
            if isinstance(resposta_pagina, list):
                pedidos_pagina = resposta_pagina
                tem_mais_paginas = False
            else:
                pedidos_pagina = resposta_pagina.get("data", [])
                total_registros = resposta_pagina.get("total", 0)
                tem_mais_paginas = (pagina_atual * tamanho_pagina) < total_registros

            todos_pedidos.extend(pedidos_pagina)

            if not tem_mais_paginas or not pedidos_pagina:
                break

            pagina_atual += 1

        logger.info(
            "Total de %d pedidos obtidos do TOTVS no período %s–%s.",
            len(todos_pedidos),
            data_inicio_str,
            data_fim_str,
        )
        return todos_pedidos

    def buscar_cliente(self, codigo_cliente: str) -> dict[str, Any] | None:
        """
        Busca dados de um cliente específico no TOTVS.

        Args:
            codigo_cliente: Código do cliente (campo A1_COD do TOTVS).

        Returns:
            Dados do cliente ou None se não encontrado.
        """
        try:
            return self._fazer_requisicao("GET", f"/api/clientes/{codigo_cliente}")
        except httpx.HTTPStatusError as excecao:
            if excecao.response.status_code == 404:
                logger.warning("Cliente '%s' não encontrado no TOTVS.", codigo_cliente)
                return None
            raise

    def buscar_estoque(self, codigo_produto: str) -> dict[str, Any] | None:
        """
        Consulta o saldo de estoque de um produto no TOTVS.

        Args:
            codigo_produto: Código do produto (campo B1_COD do TOTVS).

        Returns:
            Saldo de estoque ou None se o produto não existir.
        """
        try:
            return self._fazer_requisicao("GET", f"/api/estoque/{codigo_produto}")
        except httpx.HTTPStatusError as excecao:
            if excecao.response.status_code == 404:
                logger.warning("Produto '%s' não encontrado no TOTVS.", codigo_produto)
                return None
            raise

    def confirmar_pedido(self, numero_pedido: str) -> bool:
        """
        Confirma um pedido no TOTVS, alterando seu status para "Confirmado".

        Args:
            numero_pedido: Número do pedido (campo C5_NUM do TOTVS).

        Returns:
            True se confirmado com sucesso, False caso contrário.
        """
        corpo_confirmacao = {
            "C5_NUM": numero_pedido,
            "C5_STATUS": "S",  # S = Confirmado no TOTVS
        }

        try:
            resposta = self._fazer_requisicao(
                "POST",
                f"/api/pedidos/{numero_pedido}/confirmar",
                corpo=corpo_confirmacao,
            )
            sucesso = resposta.get("sucesso", False)
            logger.info(
                "Confirmação do pedido %s: %s",
                numero_pedido,
                "✅ Sucesso" if sucesso else "❌ Falha",
            )
            return sucesso

        except Exception:  # noqa: BLE001
            logger.exception("Erro ao confirmar pedido %s no TOTVS.", numero_pedido)
            return False
