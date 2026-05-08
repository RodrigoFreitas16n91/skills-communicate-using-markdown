"""
Agente de Integração — Plataforma de Integrações ERP/CRM
=========================================================
Descrição:
    Agente inteligente responsável por sincronizar, validar
    e transformar dados entre os sistemas ERP/CRM (TOTVS, SAP,
    Oracle) e o banco de dados local da plataforma.

    Utiliza o protocolo MCP para se comunicar com ferramentas
    externas e LangChain para lógica de decisão baseada em LLM.

Autor: Rodrigo Freitas
Versão: 1.0.0
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

import httpx

# Configuração do logger em português
logger = logging.getLogger(__name__)


# ============================================================
# ENUMERAÇÕES
# ============================================================

class SistemaOrigem(str, Enum):
    """Sistemas de origem suportados pela plataforma."""
    TOTVS = "TOTVS"
    SAP = "SAP"
    ORACLE = "ORACLE"
    DESCONHECIDO = "DESCONHECIDO"


class StatusPedido(str, Enum):
    """Status normalizados de pedidos (modelo unificado)."""
    ABERTO = "ABERTO"
    CONFIRMADO = "CONFIRMADO"
    EM_SEPARACAO = "EM_SEPARACAO"
    FATURADO = "FATURADO"
    ENTREGUE = "ENTREGUE"
    CANCELADO = "CANCELADO"
    DESCONHECIDO = "DESCONHECIDO"


class ResultadoOperacao(str, Enum):
    """Resultado de uma operação de integração."""
    SUCESSO = "SUCESSO"
    FALHA = "FALHA"
    PARCIAL = "PARCIAL"
    IGNORADO = "IGNORADO"


# ============================================================
# ESTRUTURAS DE DADOS (DATACLASSES)
# ============================================================

@dataclass
class ItemPedido:
    """Representa um item dentro de um pedido de venda."""
    codigo_produto: str
    descricao_produto: str
    quantidade: Decimal
    preco_unitario: Decimal
    valor_item: Decimal = field(init=False)

    def __post_init__(self) -> None:
        """Calcula o valor do item após a inicialização."""
        self.valor_item = self.quantidade * self.preco_unitario


@dataclass
class Pedido:
    """
    Modelo unificado de pedido de venda.

    Representa um pedido normalizado, independentemente
    do sistema de origem (TOTVS, SAP ou Oracle).
    """
    numero_pedido: str
    codigo_cliente: str
    nome_cliente: str
    data_criacao: datetime
    data_entrega: datetime | None
    valor_total: Decimal
    moeda: str
    status_pedido: StatusPedido
    sistema_origem: SistemaOrigem
    itens: list[ItemPedido] = field(default_factory=list)
    data_processamento: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadados_extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class ResultadoSincronizacao:
    """Resultado de uma execução do ciclo de sincronização."""
    sistema_origem: SistemaOrigem
    total_processados: int = 0
    total_inseridos: int = 0
    total_atualizados: int = 0
    total_ignorados: int = 0
    total_erros: int = 0
    erros: list[str] = field(default_factory=list)
    resultado: ResultadoOperacao = ResultadoOperacao.SUCESSO
    duracao_segundos: float = 0.0
    timestamp_inicio: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ============================================================
# MAPEADORES DE STATUS
# ============================================================

# Mapeamento de status do TOTVS para o modelo unificado
MAPA_STATUS_TOTVS: dict[str, StatusPedido] = {
    "L": StatusPedido.ABERTO,
    "S": StatusPedido.CONFIRMADO,
    "E": StatusPedido.EM_SEPARACAO,
    "F": StatusPedido.FATURADO,
    "D": StatusPedido.ENTREGUE,
    "X": StatusPedido.CANCELADO,
}

# Mapeamento de status do SAP para o modelo unificado
MAPA_STATUS_SAP: dict[str, StatusPedido] = {
    "A": StatusPedido.ABERTO,
    "B": StatusPedido.CONFIRMADO,
    "C": StatusPedido.ENTREGUE,
    "": StatusPedido.EM_SEPARACAO,
}

# Mapeamento de status do Oracle para o modelo unificado
MAPA_STATUS_ORACLE: dict[str, StatusPedido] = {
    "ENTERED": StatusPedido.ABERTO,
    "BOOKED": StatusPedido.CONFIRMADO,
    "PICKED": StatusPedido.EM_SEPARACAO,
    "SHIPPED": StatusPedido.ENTREGUE,
    "CANCELLED": StatusPedido.CANCELADO,
}


# ============================================================
# CLASSE PRINCIPAL: AgenteIntegracao
# ============================================================

class AgenteIntegracao:
    """
    Agente responsável pela integração entre ERPs/CRMs e
    o banco de dados local da plataforma.

    Realiza o ciclo completo:
    1. Conecta ao ERP de origem
    2. Busca dados novos/atualizados desde a última sincronização
    3. Valida e normaliza os dados para o modelo unificado
    4. Persiste os dados no banco local
    5. Registra o resultado da operação
    """

    def __init__(
        self,
        sistema: SistemaOrigem,
        url_base_erp: str,
        token_acesso_erp: str,
        url_banco_local: str,
        timeout_requisicao: int = 30,
    ) -> None:
        """
        Inicializa o agente de integração.

        Args:
            sistema: Sistema de origem dos dados (TOTVS, SAP, Oracle).
            url_base_erp: URL base da API do ERP.
            token_acesso_erp: Token de autenticação do ERP.
            url_banco_local: URL de conexão com o banco de dados local.
            timeout_requisicao: Timeout em segundos para cada requisição HTTP.
        """
        self.sistema = sistema
        self.url_base_erp = url_base_erp.rstrip("/")
        self.token_acesso_erp = token_acesso_erp
        self.url_banco_local = url_banco_local
        self.timeout_requisicao = timeout_requisicao

        # Cabeçalhos padrão para chamadas à API do ERP
        self.cabecalhos_http = {
            "Authorization": f"Bearer {self.token_acesso_erp}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.info(
            "Agente de integração inicializado. Sistema: %s | URL: %s",
            self.sistema.value,
            self.url_base_erp,
        )

    def buscar_pedidos_novos(self, desde: datetime) -> list[dict[str, Any]]:
        """
        Busca pedidos novos ou atualizados no ERP desde a data informada.

        Args:
            desde: Data/hora de corte. Retorna apenas pedidos
                   criados ou modificados após essa data.

        Returns:
            Lista de pedidos no formato raw do ERP.

        Raises:
            httpx.HTTPError: Em caso de falha na comunicação com o ERP.
        """
        # Formata a data no padrão aceito pelo ERP
        data_filtro = desde.strftime("%Y%m%d") if self.sistema == SistemaOrigem.TOTVS else desde.isoformat()

        # Mapeia os endpoints por sistema de origem
        endpoints_por_sistema = {
            SistemaOrigem.TOTVS: f"/api/pedidos?dtini={data_filtro}",
            SistemaOrigem.SAP: f"/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder?$filter=CreationDate gt {data_filtro}",
            SistemaOrigem.ORACLE: f"/fscmRestApi/resources/11.13.18.05/orders?q=CreationDate>{data_filtro}&limit=500",
        }

        url_endpoint = endpoints_por_sistema.get(self.sistema)
        if not url_endpoint:
            logger.error("Sistema '%s' não possui endpoint configurado.", self.sistema.value)
            return []

        url_completa = f"{self.url_base_erp}{url_endpoint}"
        logger.info("Buscando pedidos em: %s", url_completa)

        try:
            with httpx.Client(timeout=self.timeout_requisicao) as cliente_http:
                resposta = cliente_http.get(url_completa, headers=self.cabecalhos_http)
                resposta.raise_for_status()
                dados = resposta.json()

            # Extrai a lista de pedidos (estrutura varia por sistema)
            if self.sistema == SistemaOrigem.SAP:
                lista_pedidos = dados.get("value", [])
            elif self.sistema == SistemaOrigem.ORACLE:
                lista_pedidos = dados.get("items", [])
            else:
                lista_pedidos = dados if isinstance(dados, list) else dados.get("pedidos", [])

            logger.info(
                "Encontrados %d pedidos no %s desde %s.",
                len(lista_pedidos),
                self.sistema.value,
                desde.isoformat(),
            )
            return lista_pedidos

        except httpx.TimeoutException:
            logger.error("Timeout ao conectar ao %s (limite: %ds).", self.sistema.value, self.timeout_requisicao)
            raise
        except httpx.HTTPStatusError as excecao:
            logger.error(
                "Erro HTTP %d ao buscar pedidos do %s: %s",
                excecao.response.status_code,
                self.sistema.value,
                excecao.response.text,
            )
            raise

    def normalizar_pedido(self, dado_raw: dict[str, Any]) -> Pedido | None:
        """
        Normaliza um pedido do formato raw do ERP para o modelo unificado.

        Args:
            dado_raw: Pedido no formato original do ERP.

        Returns:
            Objeto Pedido normalizado, ou None se os dados forem inválidos.
        """
        try:
            if self.sistema == SistemaOrigem.TOTVS:
                return self._normalizar_pedido_totvs(dado_raw)
            elif self.sistema == SistemaOrigem.SAP:
                return self._normalizar_pedido_sap(dado_raw)
            elif self.sistema == SistemaOrigem.ORACLE:
                return self._normalizar_pedido_oracle(dado_raw)
            else:
                logger.warning("Sistema de origem desconhecido: %s", self.sistema)
                return None

        except (KeyError, ValueError, TypeError) as excecao:
            logger.error(
                "Erro ao normalizar pedido do %s: %s. Dado: %s",
                self.sistema.value,
                str(excecao),
                dado_raw,
            )
            return None

    def _normalizar_pedido_totvs(self, dado: dict[str, Any]) -> Pedido:
        """Normaliza pedido no formato TOTVS Protheus."""
        # Converte data no formato YYYYMMDD para datetime
        data_criacao = datetime.strptime(dado["C5_EMISSAO"], "%Y%m%d").replace(tzinfo=timezone.utc)
        data_entrega = (
            datetime.strptime(dado["C5_ENTREG"], "%Y%m%d").replace(tzinfo=timezone.utc)
            if dado.get("C5_ENTREG")
            else None
        )

        # Normaliza os itens do pedido
        itens_normalizados = [
            ItemPedido(
                codigo_produto=item["C6_PRODUTO"],
                descricao_produto=item.get("B1_DESC", "Sem descrição"),
                quantidade=Decimal(str(item["C6_QTDVEN"])),
                preco_unitario=Decimal(str(item["C6_PRCVEN"])),
            )
            for item in dado.get("itens", [])
        ]

        return Pedido(
            numero_pedido=dado["C5_NUM"].strip(),
            codigo_cliente=dado["C5_CLIENTE"].strip(),
            nome_cliente=dado.get("A1_NOME", "").strip(),
            data_criacao=data_criacao,
            data_entrega=data_entrega,
            valor_total=Decimal(str(dado["C5_VALBRUT"])),
            moeda=dado.get("C5_MOEDA", "BRL"),
            status_pedido=MAPA_STATUS_TOTVS.get(dado.get("C5_STATUS", ""), StatusPedido.DESCONHECIDO),
            sistema_origem=SistemaOrigem.TOTVS,
            itens=itens_normalizados,
        )

    def _normalizar_pedido_sap(self, dado: dict[str, Any]) -> Pedido:
        """Normaliza pedido no formato SAP OData."""
        data_criacao = datetime.fromisoformat(dado["CreationDate"]).replace(tzinfo=timezone.utc)
        data_entrega_str = dado.get("RequestedDeliveryDate")
        data_entrega = (
            datetime.fromisoformat(data_entrega_str).replace(tzinfo=timezone.utc)
            if data_entrega_str
            else None
        )

        return Pedido(
            numero_pedido=dado["SalesOrder"],
            codigo_cliente=dado["SoldToParty"],
            nome_cliente=dado.get("SoldToPartyName", ""),
            data_criacao=data_criacao,
            data_entrega=data_entrega,
            valor_total=Decimal(str(dado.get("TotalNetAmount", "0"))),
            moeda=dado.get("TransactionCurrency", "BRL"),
            status_pedido=MAPA_STATUS_SAP.get(
                dado.get("OverallDeliveryStatus", ""), StatusPedido.DESCONHECIDO
            ),
            sistema_origem=SistemaOrigem.SAP,
        )

    def _normalizar_pedido_oracle(self, dado: dict[str, Any]) -> Pedido:
        """Normaliza pedido no formato Oracle ERP Cloud REST."""
        data_criacao = datetime.fromisoformat(dado["OrderedDate"]).replace(tzinfo=timezone.utc)
        data_entrega_str = dado.get("RequestedShipDate")
        data_entrega = (
            datetime.fromisoformat(data_entrega_str).replace(tzinfo=timezone.utc)
            if data_entrega_str
            else None
        )

        return Pedido(
            numero_pedido=dado["OrderNumber"],
            codigo_cliente=dado.get("CustomerAccountNumber", ""),
            nome_cliente=dado.get("CustomerName", ""),
            data_criacao=data_criacao,
            data_entrega=data_entrega,
            valor_total=Decimal(str(dado.get("OrderedAmount", "0"))),
            moeda=dado.get("TransactionCurrencyCode", "BRL"),
            status_pedido=MAPA_STATUS_ORACLE.get(
                dado.get("StatusCode", ""), StatusPedido.DESCONHECIDO
            ),
            sistema_origem=SistemaOrigem.ORACLE,
        )

    def executar_ciclo_sincronizacao(self, desde: datetime) -> ResultadoSincronizacao:
        """
        Executa um ciclo completo de sincronização.

        Busca, normaliza e persiste todos os pedidos novos
        encontrados no ERP desde a data informada.

        Args:
            desde: Data/hora da última sincronização.

        Returns:
            ResultadoSincronizacao com estatísticas do ciclo.
        """
        resultado = ResultadoSincronizacao(sistema_origem=self.sistema)
        inicio_execucao = datetime.now(timezone.utc)

        logger.info(
            "Iniciando ciclo de sincronização. Sistema: %s | Desde: %s",
            self.sistema.value,
            desde.isoformat(),
        )

        try:
            # Etapa 1: Busca dados no ERP
            pedidos_raw = self.buscar_pedidos_novos(desde)
            resultado.total_processados = len(pedidos_raw)

            # Etapa 2: Normaliza e persiste cada pedido
            for pedido_raw in pedidos_raw:
                pedido_normalizado = self.normalizar_pedido(pedido_raw)

                if pedido_normalizado is None:
                    resultado.total_erros += 1
                    resultado.erros.append(f"Falha ao normalizar pedido: {pedido_raw.get('id', 'ID desconhecido')}")
                    continue

                # TODO: Implementar persistência real no banco de dados
                # resultado_db = repositorio_pedidos.upsert(pedido_normalizado)
                resultado.total_inseridos += 1
                logger.debug("Pedido %s sincronizado.", pedido_normalizado.numero_pedido)

            # Define resultado baseado nas estatísticas
            if resultado.total_erros == 0:
                resultado.resultado = ResultadoOperacao.SUCESSO
            elif resultado.total_erros < resultado.total_processados:
                resultado.resultado = ResultadoOperacao.PARCIAL
            else:
                resultado.resultado = ResultadoOperacao.FALHA

        except Exception as excecao:  # noqa: BLE001
            resultado.resultado = ResultadoOperacao.FALHA
            resultado.erros.append(str(excecao))
            logger.exception("Erro crítico durante sincronização do %s.", self.sistema.value)

        finally:
            # Calcula duração total do ciclo
            fim_execucao = datetime.now(timezone.utc)
            resultado.duracao_segundos = (fim_execucao - inicio_execucao).total_seconds()

            logger.info(
                "Ciclo concluído. Resultado: %s | Total: %d | OK: %d | Erros: %d | Duração: %.2fs",
                resultado.resultado.value,
                resultado.total_processados,
                resultado.total_inseridos,
                resultado.total_erros,
                resultado.duracao_segundos,
            )

        return resultado


# ============================================================
# FÁBRICA DE AGENTES
# ============================================================

def criar_agente_por_sistema(sistema: SistemaOrigem) -> AgenteIntegracao:
    """
    Cria e retorna um agente de integração configurado para
    o sistema especificado, usando variáveis de ambiente.

    Args:
        sistema: Sistema de origem desejado.

    Returns:
        Instância configurada de AgenteIntegracao.

    Raises:
        ValueError: Se o sistema não for suportado.
        EnvironmentError: Se variáveis de ambiente obrigatórias estiverem ausentes.
    """
    # Mapeamento de configurações por sistema
    configuracoes_por_sistema = {
        SistemaOrigem.TOTVS: {
            "url_base_erp": os.environ["TOTVS_URL_BASE"],
            "token_acesso_erp": os.environ["TOTVS_TOKEN_ACESSO"],
            "timeout_requisicao": int(os.environ.get("TOTVS_TIMEOUT_SEGUNDOS", "30")),
        },
        SistemaOrigem.SAP: {
            "url_base_erp": os.environ["SAP_URL_BASE"],
            "token_acesso_erp": os.environ["SAP_TOKEN_ACESSO"],
            "timeout_requisicao": int(os.environ.get("SAP_TIMEOUT_SEGUNDOS", "60")),
        },
        SistemaOrigem.ORACLE: {
            "url_base_erp": os.environ["ORACLE_URL_BASE"],
            "token_acesso_erp": os.environ["ORACLE_TOKEN_ACESSO"],
            "timeout_requisicao": int(os.environ.get("ORACLE_TIMEOUT_SEGUNDOS", "45")),
        },
    }

    configuracao = configuracoes_por_sistema.get(sistema)
    if not configuracao:
        raise ValueError(f"Sistema '{sistema.value}' não é suportado pela fábrica de agentes.")

    return AgenteIntegracao(
        sistema=sistema,
        url_banco_local=os.environ["DATABASE_URL"],
        **configuracao,
    )
