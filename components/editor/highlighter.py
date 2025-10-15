# components/editor/highlighter.py

"""
Este módulo define o HtmlHighlighter, responsável por aplicar o realce de
sintaxe (syntax highlighting) para código HTML em um QTextDocument.
"""

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QTextCharFormat, QSyntaxHighlighter

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