# Arquivo: components.py

import re
import os
from PySide6.QtCore import Signal, QRegularExpression, Qt, QRect, QSize, QTimer
from PySide6.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter, QAction, QPainter, QKeySequence
from PySide6.QtWidgets import (QPlainTextEdit, QMenu, QApplication, QWidget, QTextEdit, QVBoxLayout, 
                               QTableWidget, QHeaderView, QTableWidgetItem, QPushButton, QSplitter, QHBoxLayout)
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineUrlRequestInterceptor, QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView

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

class NetworkPanel(QWidget):
    """
    Um widget de painel que exibe um log de requisições de rede interceptadas.
    """
    # Sinal emitido quando o utilizador solicita a edição de uma requisição específica.
    request_tamper_requested = Signal(dict)

    def __init__(self, parent=None):
        """Construtor da classe NetworkPanel."""
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        
        # Tabela para exibir os dados das requisições.
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Método", "URL", "Status"])
        # Configura a coluna da URL para expandir e preencher o espaço disponível.
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Botão para limpar o log de requisições.
        clear_button = QPushButton("Limpar")
        clear_button.clicked.connect(self.clear_log)
        
        self.layout().addWidget(self.table)
        self.layout().addWidget(clear_button)
        
        # Habilita a política de menu de contexto para permitir ações de clique direito.
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.abrir_menu_contexto)

    def add_request(self, info: dict):
        """
        Slot público para adicionar uma nova entrada de requisição à tabela.

        Args:
            info (dict): Dicionário contendo os detalhes da requisição.
        """
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)

        method_item = QTableWidgetItem(info["method"])
        url_item = QTableWidgetItem(info["url"])
        
        # Armazena o dicionário completo da requisição no item da URL usando UserRole.
        # Isso permite a recuperação dos dados completos posteriormente (ex: no menu de contexto).
        url_item.setData(Qt.UserRole, info)
        
        # Formatação condicional para o status da requisição.
        if info["blocked"]:
            status_item = QTableWidgetItem("Bloqueado")
            status_item.setForeground(QColor("red"))
        else:
            status_item = QTableWidgetItem("Permitido")
            status_item.setForeground(QColor("green"))

        self.table.setItem(row_position, 0, method_item)
        self.table.setItem(row_position, 1, url_item)
        self.table.setItem(row_position, 2, status_item)
        self.table.scrollToBottom()

    def clear_log(self):
        """Remove todas as entradas da tabela de requisições."""
        self.table.setRowCount(0)

    def abrir_menu_contexto(self, position):
        """
        Cria e exibe um menu de contexto quando o utilizador clica com o botão direito na tabela.
        """
        item = self.table.itemAt(position)
        if not item: return

        # Recupera os dados completos da requisição armazenados no item.
        request_info = self.table.item(item.row(), 1).data(Qt.UserRole)
        
        # Cria o menu e suas ações.
        menu = QMenu()
        edit_action = QAction("Editar e Reenviar", self)
        # Conecta a ação para emitir um sinal com os dados da requisição.
        edit_action.triggered.connect(lambda: self.request_tamper_requested.emit(request_info))
        menu.addAction(edit_action)
        menu.exec(self.table.viewport().mapToGlobal(position))

class HtmlHighlighter(QSyntaxHighlighter):
    """
    Implementa o realce de sintaxe para código HTML dentro de um QTextDocument.
    """
    def __init__(self, parent=None):
        """Construtor da classe HtmlHighlighter."""
        super().__init__(parent)
        self.highlighting_rules = []

        # Define o formato para tags HTML (ex: <div>, </span>).
        tag_format = QTextCharFormat(); tag_format.setForeground(QColor("#0000FF"))
        self.highlighting_rules.append((QRegularExpression(r"<[/]?[a-zA-Z0-9_:]+\b"), tag_format))
        self.highlighting_rules.append((QRegularExpression(r">"), tag_format))
        
        # Define o formato para atributos de tags (ex: class=, href=).
        attribute_format = QTextCharFormat(); attribute_format.setForeground(QColor("#FF0000"))
        self.highlighting_rules.append((QRegularExpression(r'\s+[a-zA-Z0-9_-]+='), attribute_format))
        
        # Define o formato para valores de atributos (texto entre aspas).
        value_format = QTextCharFormat(); value_format.setForeground(QColor("#800080"))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), value_format))
        self.highlighting_rules.append((QRegularExpression(r"'[^']*'"), value_format))
        
        # Define o formato para comentários HTML ().
        comment_format = QTextCharFormat(); comment_format.setForeground(QColor("#008000"))
        self.highlighting_rules.append((QRegularExpression(r""), comment_format))

    def highlightBlock(self, text: str):
        """
        Método de callback executado pelo Qt para aplicar o realce a um bloco de texto.

        Args:
            text (str): O conteúdo do bloco de texto a ser formatado.
        """
        for pattern, format in self.highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

class LineNumberArea(QWidget):
    """
    Widget auxiliar que renderiza a área de números de linha para um editor de texto.
    """
    def __init__(self, editor):
        """
        Construtor da classe LineNumberArea.

        Args:
            editor (HtmlEditor): A instância do editor de texto ao qual esta área pertence.
        """
        super().__init__(editor)
        self.editor = editor

    def sizeHint(self):
        """Retorna a largura calculada necessária para a área de números de linha."""
        return QSize(self.editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        """
        Evento de pintura que delega a renderização para o widget do editor principal.
        """
        self.editor.line_number_area_paint_event(event)

class HtmlEditor(QPlainTextEdit):
    """
    Um widget de editor de texto otimizado para edição de código HTML,
    com funcionalidades de realce de sintaxe e exibição de números de linha.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFont(QFont("Courier New", 10))
        self.setStyleSheet("background-color: #FFFFFF; color: #000000;")
        
        # Instancia e aplica o realce de sintaxe.
        self.highlighter = HtmlHighlighter(self.document())
        
        # Instancia a área de números de linha.
        self.line_number_area = LineNumberArea(self)

        # Conecta sinais internos para manter a área de números de linha sincronizada.
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_line_number_area_width(0)
        self.highlight_current_line()

    def line_number_area_width(self):
        """Calcula a largura em pixels necessária para exibir o maior número de linha."""
        digits = len(str(max(1, self.blockCount())))
        space = 10 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        """Define a margem esquerda do editor para acomodar a área de números de linha."""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        """Redesenha a área de números de linha em resposta a rolagem ou outras atualizações."""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        """Sobrescreve o evento de redimensionamento para ajustar a geometria da área de números de linha."""
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        """
        Lógica de renderização para a área de números de linha.

        Este método é chamado pelo `paintEvent` do widget `LineNumberArea`.
        """
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#F0F0F0"))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        # Itera sobre todos os blocos de texto visíveis e desenha seus números de linha.
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(Qt.darkGray)
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(), Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        """Aplica um fundo de destaque à linha onde o cursor está posicionado."""
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(QColor("#E8E8E8"))
            selection.format.setProperty(QTextCharFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

class SplitEditor(QWidget):
    """
    Um widget composto que integra um editor de código (`HtmlEditor`) e uma
    pré-visualização web (`WebView`) lado a lado, utilizando um `QSplitter`.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        
        self.editor = HtmlEditor()
        self.preview = WebView(parent)
        
        splitter.addWidget(self.editor)
        splitter.addWidget(self.preview)
        splitter.setSizes([self.width() // 2, self.width() // 2])
        
        self.layout().addWidget(splitter)
        
        # Utiliza um QTimer para implementar "debouncing", evitando atualizações
        # da pré-visualização a cada tecla pressionada, melhorando a performance.
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(300) # Intervalo de 300ms
        self.update_timer.timeout.connect(self._do_update_preview)
        
        self.editor.textChanged.connect(self.schedule_preview_update)
        
        # Garante uma pré-visualização inicial ao criar o widget.
        self._do_update_preview()

    def schedule_preview_update(self):
        """Reinicia o temporizador de atualização a cada alteração no texto."""
        self.update_timer.start()

    def _do_update_preview(self):
        """Atualiza o conteúdo HTML da pré-visualização quando o temporizador expira."""
        self.preview.setHtml(self.editor.toPlainText())

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