# components/network/interceptor.py

"""
Este módulo define o UrlInterceptor, um componente de baixo nível que
interceta todas as requisições de rede feitas pelo motor web.
"""

from PySide6.QtCore import Signal
from PySide6.QtWebEngineCore import QWebEngineUrlRequestInterceptor

class UrlInterceptor(QWebEngineUrlRequestInterceptor):
    """
    Intercepta todas as requisições de rede originadas pelo QWebEngine.

    Esta classe atua como um middleware, permitindo a inspeção de cada requisição antes
    de ela ser executada. É fundamental para funcionalidades como o painel de rede e o
    bloqueio de conteúdo, emitindo um sinal com os detalhes de cada requisição.
    """
    # Sinal emitido para cada requisição interceptada, contendo seus detalhes.
    # O payload é um dicionário com informações como URL, método e status de bloqueio.
    requestIntercepted = Signal(dict)

    def __init__(self, blocklist, parent=None):
        """
        Construtor da classe UrlInterceptor.

        Args:
            blocklist (set): Um conjunto de domínios a serem bloqueados.
            parent (QObject, optional): O objeto pai no sistema de memória do Qt.
        """
        super().__init__(parent)
        self.blocklist = blocklist
        # Flag de estado para ativar ou desativar o mecanismo de bloqueio dinamicamente.
        self.blocking_enabled = False

    def interceptRequest(self, info):
        """
        Método de callback executado pelo Qt para cada requisição de rede.

        Este método analisa a URL, verifica se o host corresponde a um domínio na
        'blocklist' (se o bloqueio estiver ativo) e emite o sinal `requestIntercepted`
        com os metadados da requisição.

        Args:
            info (QWebEngineUrlRequestInfo): Objeto fornecido pelo Qt com os detalhes da requisição.
        """
        url_str = info.requestUrl().toString()
        host = info.requestUrl().host()
        method = info.requestMethod().data().decode('utf-8')

        # Verifica se o bloqueio de conteúdo está habilitado.
        if self.blocking_enabled:
            for blocked_domain in self.blocklist:
                # Compara o host da requisição com os domínios da blocklist.
                if host == blocked_domain or host.endswith("." + blocked_domain):
                    print(f"[BLOQUEADO] Bloqueando requisição para: {host}")
                    info.block(True)  # Instrui o WebEngine a bloquear a requisição.
                    self.requestIntercepted.emit({
                        "url": url_str, "method": method, "headers": {}, "body": "", "blocked": True
                    })
                    return  # Interrompe o processamento para esta requisição.

        # Se a requisição não foi bloqueada, emite o sinal com status 'permitido'.
        self.requestIntercepted.emit({
            "url": url_str, "method": method, "headers": {}, "body": "", "blocked": False
        })