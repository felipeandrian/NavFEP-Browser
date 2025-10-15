# components/editor/line_number.py

"""
Este módulo define o LineNumberArea, um widget auxiliar que renderiza a
área de números de linha para um editor de texto.
"""

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QWidget

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