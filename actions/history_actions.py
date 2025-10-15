# actions/history_actions.py

"""
Este módulo contém o mixin HistoryActions, responsável por todas as operações
relacionadas com o histórico de navegação.

As suas responsabilidades incluem:
- Carregar e salvar o histórico de navegação para um ficheiro JSON.
- Adicionar novas entradas ao histórico à medida que o utilizador navega.
- Construir e gerir uma aba de interface de utilizador para exibir, pesquisar e
  limpar o histórico.
"""

# --- Imports da Biblioteca Padrão ---
import json
import datetime

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLineEdit, QListWidget, 
                               QListWidgetItem, QPushButton, QMessageBox)

# --- Imports Locais da Aplicação ---
# A classe depende do WebView para obter informações da página atual.
from components import WebView

class HistoryActions:
    """
    Mixin para as ações de Histórico de Navegação.

    Responsabilidades:
    - Carregar e salvar o histórico em arquivo JSON.
    - Registrar novas entradas de navegação.
    - Exibir o histórico em uma aba dedicada, com filtro de pesquisa.
    - Permitir limpar o histórico e reabrir páginas visitadas.
    """

    def carregar_historico(self):
        """
        Carrega o histórico de navegação a partir de um arquivo JSON.

        - Caso o arquivo exista e seja válido, carrega a lista de entradas.
        - Caso contrário, inicializa o histórico como uma lista vazia.
        """
        try:
            with open(self.history_file, "r", encoding='utf-8') as f:
                self.history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []

    def salvar_historico(self):
        """
        Salva o histórico de navegação no arquivo JSON.

        - Garante persistência entre sessões.
        - Usa indentação para facilitar leitura manual do arquivo.
        """
        with open(self.history_file, "w", encoding='utf-8') as f:
            json.dump(self.history, f, indent=4)

    def adicionar_ao_historico(self, browser):
        """
        Adiciona a página atual ao histórico de navegação.

        - Obtém a URL e o título da aba atual.
        - Ignora URLs inválidas, em branco ou duplicadas consecutivas.
        - Cria uma entrada com URL, título e timestamp ISO 8601.
        - Salva o histórico atualizado em arquivo.
        """
        url = browser.url().toString()
        titulo = browser.title()

        if not url or url == "about:blank" or (self.history and self.history[-1]['url'] == url):
            return

        entrada = {
            "url": url,
            "titulo": titulo,
            "timestamp": datetime.datetime.now().isoformat()
        }
        self.history.append(entrada)
        self.salvar_historico()

    def abrir_aba_historico(self):
        """
        Abre uma nova aba exibindo o histórico de navegação.

        - Se a aba "Histórico" já estiver aberta, apenas a ativa.
        - Caso contrário:
            - Cria um widget com campo de filtro, lista de histórico e botão de limpar.
            - Popula a lista com entradas do histórico em ordem reversa (mais recentes primeiro).
            - Cada item exibe título, data/hora formatada e URL.
            - Permite abrir páginas ao dar duplo clique em um item.
            - Permite filtrar entradas digitando no campo de pesquisa.
        """
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == "Histórico":
                self.tabs.setCurrentIndex(i)
                return

        history_widget = QWidget()
        layout = QVBoxLayout(history_widget)

        filter_input = QLineEdit()
        filter_input.setPlaceholderText("Pesquisar no histórico...")

        self.history_list_widget = QListWidget()

        # Botão para limpar histórico
        btn_limpar = QPushButton("Limpar Histórico")
        btn_limpar.clicked.connect(self.limpar_historico)

        layout.addWidget(filter_input)
        layout.addWidget(self.history_list_widget)
        layout.addWidget(btn_limpar)

        # Popula a lista com entradas do histórico
        for item in reversed(self.history):
            try:
                dt_object = datetime.datetime.fromisoformat(item['timestamp'])
                formatted_time = dt_object.strftime('%d/%m/%Y %H:%M:%S')
                display_text = f"{item['titulo']}\n{formatted_time} - {item['url']}"
            except (ValueError, KeyError):
                display_text = f"{item.get('titulo', 'Sem Título')}\n{item.get('url', '')}"

            list_item = QListWidgetItem(display_text)
            list_item.setData(Qt.UserRole, item['url'])
            self.history_list_widget.addItem(list_item)

        # Conexões de eventos
        self.history_list_widget.itemDoubleClicked.connect(self._on_history_item_activated)
        filter_input.textChanged.connect(self._filter_history)

        index = self.tabs.addTab(history_widget, "Histórico")
        self.tabs.setCurrentIndex(index)

    def limpar_historico(self):
        """
        Limpa todo o histórico de navegação.

        - Remove todas as entradas da lista em memória.
        - Atualiza o arquivo JSON para refletir a exclusão.
        - Limpa a lista exibida na interface, se existir.
        """
        self.history.clear()
        self.salvar_historico()
        if hasattr(self, 'history_list_widget'):
            self.history_list_widget.clear()
        print("Histórico limpo.")

    def _on_history_item_activated(self, item):
        """
        Abre em uma nova aba a URL associada ao item do histórico.

        - Obtém a URL armazenada no item da lista.
        - Cria uma nova aba de navegação com essa URL.
        """
        url = item.data(Qt.UserRole)
        self.adicionar_nova_aba(QUrl(url))

    def _filter_history(self, text):
        """
        Filtra os itens do histórico exibidos na lista.

        - Esconde os itens cujo texto não contenha o termo pesquisado.
        - A busca é case-insensitive (ignora maiúsculas/minúsculas).
        """
        for i in range(self.history_list_widget.count()):
            item = self.history_list_widget.item(i)
            item.setHidden(text.lower() not in item.text().lower())