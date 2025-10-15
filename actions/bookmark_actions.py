# actions/bookmark_actions.py

"""
Este módulo contém o mixin BookmarkActions, responsável por toda a lógica
relacionada com a gestão de favoritos (bookmarks).

As suas responsabilidades incluem:
- Carregar e salvar os favoritos para um ficheiro JSON.
- Implementar as operações de CRUD (Create, Read, Update, Delete) para os favoritos.
- Sincronizar o estado da UI (barra de favoritos e botão de alternância) com os dados.
"""

# --- Imports da Biblioteca Padrão ---
import json

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QPushButton

# --- Imports Locais da Aplicação ---
# A classe depende do WebView para obter informações da página atual.
from components import WebView

class BookmarkActions:
    """
    Classe responsável por gerenciar os favoritos (bookmarks) do navegador.
    Inclui métodos para carregar, salvar, adicionar, remover e atualizar a barra de favoritos.
    """

    def carregar_favoritos(self):
        """
        Carrega os favoritos a partir de um arquivo JSON.

        - Caso o arquivo não exista ou esteja corrompido, inicializa um dicionário vazio.
        - Estrutura esperada: { "Título da Página": "URL" }
        """
        try:
            with open(self.bookmarks_file, "r") as f:
                self.bookmarks = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.bookmarks = {}

    def salvar_favoritos(self):
        """
        Salva os favoritos atuais em um arquivo JSON.

        - Garante persistência entre sessões.
        - Usa indentação para facilitar leitura manual do arquivo.
        """
        with open(self.bookmarks_file, "w") as f:
            json.dump(self.bookmarks, f, indent=4)

    def toggle_favorito(self):
        """
        Alterna o estado de favorito da aba atual.

        - Se a URL já estiver salva nos favoritos, remove.
        - Caso contrário, adiciona como novo favorito.
        """
        aba = self.aba_atual()
        if not isinstance(aba, WebView):
            return

        url_atual = aba.url().toString()
        if url_atual in self.bookmarks.values():
            self.remover_favorito()
        else:
            self.adicionar_favorito()

    def adicionar_favorito(self):
        """
        Adiciona a aba atual à lista de favoritos.

        - Usa o título da página como chave e a URL como valor.
        - Ignora páginas sem título, sem URL ou em branco (about:blank).
        - Atualiza a barra de favoritos e o botão de alternância.
        """
        aba = self.aba_atual()
        titulo = aba.page().title()
        url = aba.url().toString()

        if not titulo or not url or url == "about:blank":
            return

        self.bookmarks[titulo] = url
        self.salvar_favoritos()
        self.atualizar_barra_favoritos()
        self.atualizar_botao_favorito()

    def remover_favorito(self):
        """
        Remove a aba atual da lista de favoritos.

        - Busca a URL atual nos favoritos e remove a entrada correspondente.
        - Atualiza a barra de favoritos e o botão de alternância.
        """
        aba = self.aba_atual()
        url_atual = aba.url().toString()
        titulo_para_remover = None

        for titulo, url in self.bookmarks.items():
            if url == url_atual:
                titulo_para_remover = titulo
                break

        if titulo_para_remover:
            del self.bookmarks[titulo_para_remover]
            self.salvar_favoritos()
            self.atualizar_barra_favoritos()
            self.atualizar_botao_favorito()

    def atualizar_botao_favorito(self):
        """
        Atualiza o estado visual do botão de favoritos.

        - Se a aba atual for uma WebView válida, habilita o botão.
        - Exibe "☆ Remover" caso a URL já esteja salva.
        - Exibe "★ Salvar" caso a URL ainda não esteja nos favoritos.
        - Caso não seja uma aba de navegação, desabilita o botão.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            self.btn_toggle_favorito.setEnabled(True)
            url_atual = aba.url().toString()
            if url_atual in self.bookmarks.values():
                self.btn_toggle_favorito.setText("☆ Remover")
            else:
                self.btn_toggle_favorito.setText("★ Salvar")
        else:
            self.btn_toggle_favorito.setEnabled(False)

    def atualizar_barra_favoritos(self):
        """
        Atualiza a barra de favoritos exibida na interface.

        - Remove todos os botões atuais.
        - Cria um botão para cada favorito salvo, com o título como rótulo.
        - Cada botão abre a respectiva URL em uma nova aba ao ser clicado.
        """
        self.bookmarks_toolbar.clear()
        for titulo, url in self.bookmarks.items():
            btn = QPushButton(titulo)
            btn.clicked.connect(lambda checked, u=url: self.adicionar_nova_aba(QUrl(u)))
            self.bookmarks_toolbar.addWidget(btn)