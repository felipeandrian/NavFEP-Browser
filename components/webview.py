# components/webview.py

"""
Este módulo define o componente WebView, o widget central para a renderização
de conteúdo web no navegador.

A classe WebView estende a QWebEngineView padrão do PySide6 para adicionar
funcionalidades personalizadas, como um menu de contexto customizado e um
sistema de sinais para comunicação desacoplada com a janela principal.
"""

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QMenu
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

class WebView(QWebEngineView):
    """
    Uma subclasse de `QWebEngineView` que estende a funcionalidade padrão com
    um menu de contexto personalizado e sinais para uma comunicação desacoplada
    com a janela principal da aplicação.
    """
    # Sinais para comunicar ações do utilizador à janela principal.
    codigoFonteDisponivel = Signal(str)
    new_tab_requested = Signal()
    history_requested = Signal()
    editor_requested = Signal()
    network_panel_toggled = Signal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurações padrão para o motor web, como habilitar plugins e o visualizador de PDF.
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, True)
        if hasattr(QWebEngineSettings.WebAttribute, "PdfViewerEnabled"):
            settings.setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

    def contextMenuEvent(self, event):
        """
        Sobrescreve o manipulador de eventos do menu de contexto para exibir um menu personalizado.
        """
        menu = QMenu(self)
        
        # Ações padrão de navegação e ferramentas.
        # Ações como "Voltar" e "Avançar" são habilitadas/desabilitadas com base no estado do histórico de navegação.
        menu.addAction(QAction("Abrir Nova Aba", self, shortcut="Ctrl+T", triggered=self.new_tab_requested.emit))
        menu.addAction(QAction("Histórico", self, shortcut="Ctrl+H", triggered=self.history_requested.emit))
        menu.addSeparator()
        menu.addAction(QAction("Voltar", self, triggered=self.back, enabled=self.page().history().canGoBack()))
        menu.addAction(QAction("Avançar", self, triggered=self.forward, enabled=self.page().history().canGoForward()))
        menu.addAction(QAction("Recarregar", self, shortcut="F5", triggered=self.reload))
        menu.addSeparator()
        menu.addAction(QAction("Ver Código-Fonte", self, shortcut="Ctrl+U", triggered=self.ver_codigo_fonte))
        menu.addAction(QAction("Painel de Rede", self, shortcut="Ctrl+Shift+I", triggered=self.network_panel_toggled.emit))
        menu.addAction(QAction("Novo Editor", self, shortcut="Ctrl+N", triggered=self.editor_requested.emit))
        
        menu.exec(event.globalPos())

    def ver_codigo_fonte(self):
        """
        Inicia o processo assíncrono para obter o código-fonte HTML da página atual.
        """
        # A obtenção do HTML é uma operação assíncrona; o resultado será passado para o callback.
        self.page().toHtml(self.emitir_sinal_codigo_fonte)
        
    def emitir_sinal_codigo_fonte(self, html: str):
        """
        Callback que é executado quando o HTML está disponível. Emite o sinal
        `codigoFonteDisponivel` com o HTML como payload.

        Args:
            html (str): O código-fonte HTML da página.
        """
        self.codigoFonteDisponivel.emit(html)