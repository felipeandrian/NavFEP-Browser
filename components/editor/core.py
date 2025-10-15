# components/editor/core.py

"""
Este módulo contém os componentes centrais do editor de código:
- HtmlEditor: Um editor de texto com números de linha e realce de sintaxe.
- SplitEditor: Um widget que combina o HtmlEditor e um WebView para pré-visualização.
"""

from PySide6.QtCore import Qt, QRect, QTimer
from PySide6.QtGui import QFont, QPainter, QColor, QTextCharFormat
from PySide6.QtWidgets import QPlainTextEdit, QTextEdit, QSplitter, QWidget, QHBoxLayout

# Imports locais do pacote 'editor'
from .highlighter import HtmlHighlighter
from .line_number import LineNumberArea

# Import de outro pacote de componentes
from ..webview import WebView

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