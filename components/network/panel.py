# components/network/panel.py

"""
Este módulo define o NetworkPanel, a interface de utilizador (UI) para
exibir o log de requisições de rede.
"""

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QAction
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QHeaderView, 
                               QTableWidgetItem, QPushButton, QMenu)
							   
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