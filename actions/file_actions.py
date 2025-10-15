# actions/file_actions.py

"""
Este módulo contém o mixin FileMenuActions.

Esta classe é responsável por:
1. Construir e configurar a barra de menus principal da aplicação (Arquivo, Exibir, etc.).
2. Implementar a lógica para as ações contidas nesses menus, como abrir/salvar ficheiros.
3. Gerir o ciclo de vida das configurações de proxy (carregar, salvar, alternar).
"""

# --- Imports da Biblioteca Padrão ---
import os
import json

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QFileDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtNetwork import QNetworkProxy

# --- Imports Locais da Aplicação ---
# Estes imports referem-se a outros ficheiros do seu projeto.
from dialogs import ProxyDialog
from components import SplitEditor, HtmlEditor

class FileMenuActions:
    """Mixin que implementa as ações do menu 'Arquivo', 'Ferramentas' e relacionados."""

    def carregar_proxies(self):
        """
        Carrega a lista de proxies a partir de um arquivo JSON.
        Caso o arquivo não exista ou esteja corrompido, inicializa uma lista vazia.
        """
        try:
            with open(self.proxies_file, "r") as f:
                self.proxy_list = json.load(f)
            if self.proxy_list:
                print(f"{len(self.proxy_list)} proxies carregados de '{self.proxies_file}'.")
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Arquivo '{self.proxies_file}' não encontrado ou inválido. "
                  "Começando com lista de proxies vazia.")
            self.proxy_list = []

    def salvar_proxies(self):
        """
        Salva a lista de proxies atual em um arquivo JSON.
        """
        with open(self.proxies_file, "w") as f:
            json.dump(self.proxy_list, f, indent=4)
        print("Lista de proxies salva.")

    def criar_menus(self):
        """
        Cria e configura todos os menus principais da aplicação:
        Arquivo, Exibir, Ferramentas, Histórico e Ajuda.
        Também define atalhos de teclado e conecta ações aos métodos correspondentes.
        """
        menu_bar = self.menuBar()

        # --- Menu Arquivo ---
        file_menu = menu_bar.addMenu("&Arquivo")
        open_page_action = QAction("Abrir Página Local...", self)
        open_page_action.setShortcut(QKeySequence("Ctrl+Shift+O"))
        open_page_action.triggered.connect(self.abrir_pagina_local)
        file_menu.addAction(open_page_action)

        open_editor_action = QAction("Abrir no Editor...", self)
        open_editor_action.setShortcut(QKeySequence("Ctrl+O"))
        open_editor_action.triggered.connect(self.abrir_arquivo_no_editor)
        file_menu.addAction(open_editor_action)

        self.save_action = QAction("&Salvar Como...", self)
        self.save_action.setShortcut(QKeySequence("Ctrl+S"))
        self.save_action.triggered.connect(self.salvar_arquivo)
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()
        quit_action = QAction("&Sair", self)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # --- Menu Exibir ---
        view_menu = menu_bar.addMenu("E&xibir")

        # Alternar tela cheia
        self.fullscreen_action = QAction("Tela Cheia\tF11", self, checkable=True)
        self.fullscreen_action.toggled.connect(self.toggle_full_screen)
        view_menu.addAction(self.fullscreen_action)
        view_menu.addSeparator()

        # Alternar visibilidade das barras de ferramentas
        self.toggle_menu_bar_action = QAction("Exibir Barra de Menus\tCtrl+M", self, checkable=True)
        self.toggle_menu_bar_action.setChecked(True)
        self.toggle_menu_bar_action.toggled.connect(lambda checked: self.menuBar().setVisible(checked))
        view_menu.addAction(self.toggle_menu_bar_action)

        self.toggle_nav_bar_action = QAction("Exibir Barra de Navegação\tCtrl+Shift+L", self, checkable=True)
        self.toggle_nav_bar_action.setChecked(True)
        self.toggle_nav_bar_action.toggled.connect(lambda checked: self.nav_toolbar.setVisible(checked))
        view_menu.addAction(self.toggle_nav_bar_action)

        self.toggle_bookmarks_bar_action = QAction("Exibir Barra de Favoritos\tCtrl+Shift+B", self, checkable=True)
        self.toggle_bookmarks_bar_action.setChecked(True)
        self.toggle_bookmarks_bar_action.toggled.connect(lambda checked: self.bookmarks_toolbar.setVisible(checked))
        view_menu.addAction(self.toggle_bookmarks_bar_action)

        view_menu.addSeparator()

        # Ações de zoom
        zoom_in_action = QAction("Aumentar Zoom\tCtrl++", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Diminuir Zoom\tCtrl+-", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("Restaurar Zoom Padrão\tCtrl+0", self)
        zoom_reset_action.triggered.connect(self.zoom_reset)
        view_menu.addAction(zoom_reset_action)

        # --- Menu Ferramentas ---
        tools_menu = menu_bar.addMenu("&Ferramentas")
        proxy_action = QAction("Gerenciar Proxies...", self)
        proxy_action.triggered.connect(self.abrir_dialogo_proxy)
        tools_menu.addAction(proxy_action)

        ia_panel_action = QAction("Assistente IA", self)
        ia_panel_action.triggered.connect(self.abrir_painel_ia)
        tools_menu.addAction(ia_panel_action)

        network_action = QAction("Painel de Rede", self)
        network_action.triggered.connect(self.toggle_network_panel)
        tools_menu.addAction(network_action)

        # --- Menu Histórico ---
        history_menu = menu_bar.addMenu("Hi&stórico")
        show_history_action = QAction("Ver Histórico Completo\tCtrl+H", self)
        show_history_action.triggered.connect(self.abrir_aba_historico)
        history_menu.addAction(show_history_action)

        # --- Menu Ajuda ---
        help_menu = menu_bar.addMenu("A&juda")
        about_action = QAction("Sobre o Navegador do FEP", self)
        about_action.triggered.connect(self.abrir_janela_sobre)
        help_menu.addAction(about_action)

    def abrir_janela_sobre(self):
        """
        Exibe uma janela de diálogo 'Sobre' com informações do navegador.

        Responsabilidades:
        - Mostrar nome, versão e descrição do navegador.
        - Destacar recursos principais (ex.: suporte a Gopher, editor, IA).
        - Exibir ícone da aplicação.
        - Fornecer botão de fechamento amigável.
        """
        msg_box = QMessageBox(self)
        msg_box.setIconPixmap(self.windowIcon().pixmap(64, 64))
        msg_box.setWindowTitle("Sobre o Navegador do FEP")

        # Título principal
        msg_box.setText("<h2 style='margin:0;'>🌐 Navegador do FEP</h2>")

        # Texto informativo com HTML formatado
        msg_box.setInformativeText(
            "<p><b>Versão:</b> 1.0</p>"
            "<p>Um navegador web customizado com ferramentas avançadas:</p>"
            "<ul>"
            "<li>📝 Editor de código integrado</li>"
            "<li>📡 Painel de rede para inspeção</li>"
            "<li>🤖 Assistente de IA embutido</li>"
            "<li>🐇 Suporte ao protocolo <b>Gopher</b></li>"
            "<li>📄 Visualizador de PDFs integrado</li>"
            "</ul>"
            "<hr>"
            "<p><b>Autor:</b> Felipe Andrian Peixoto</p>"
            "<p style='font-size:10pt; color:gray;'>"
            "Desenvolvido em Python + QtWebEngine"
            "</p>"
        )

        # Botão de fechar
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.button(QMessageBox.Ok).setText("Fechar")

        msg_box.exec()

    def abrir_painel_ia(self):
        """
        Alterna a exibição do painel lateral de Assistente IA.
        """
        if self.ai_dock.isVisible():
            self.ai_dock.hide()
        else:
            self.ai_dock.show()

    def abrir_arquivo_no_editor(self):
        """
        Abre um arquivo de texto/HTML no editor embutido.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo no Editor", "",
            "Arquivos HTML (*.html *.htm);;Arquivos de Texto (*.txt);;Todos os Arquivos (*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                file_name = os.path.basename(file_path)
                self.abrir_editor_html(content=content, title=file_name)
            except Exception as e:
                print(f"Erro ao abrir o arquivo: {e}")

    def abrir_pagina_local(self):
        """
        Abre uma página HTML local em uma nova aba do navegador.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Página Local", "",
            "Arquivos HTML (*.html *.htm);;Todos os Arquivos (*)"
        )
        if file_path:
            local_url = QUrl.fromLocalFile(file_path)
            self.adicionar_nova_aba(local_url)

    def salvar_arquivo(self):
        """
        Salva o conteúdo do editor atual em um arquivo escolhido pelo usuário.
        Suporta tanto SplitEditor quanto HtmlEditor.
        """
        aba = self.aba_atual()

        # Identifica o tipo de editor ativo
        editor_instance = None
        if isinstance(aba, SplitEditor):
            editor_instance = aba.editor
        elif isinstance(aba, HtmlEditor):
            editor_instance = aba

        if not editor_instance:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Como...", "",
            "Arquivos HTML (*.html *.htm);;Arquivos de Texto (*.txt)"
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(editor_instance.toPlainText())
                self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(file_path))
            except Exception as e:
                print(f"Erro ao salvar o arquivo: {e}")

    def abrir_dialogo_proxy(self):
        """
        Abre a janela de gerenciamento de proxies, permitindo configurar
        proxies temporários, salvar novos ou desativar o uso de proxy.
        """
        dialog = ProxyDialog(self)
        dialog.temp_use_button.clicked.connect(lambda: self.definir_proxy_temporario(dialog))
        dialog.save_and_use_button.clicked.connect(lambda: self.salvar_e_usar_proxy(dialog))
        dialog.disable_button.clicked.connect(self.desativar_proxy)
        dialog.show()

    def get_proxy_from_dialog(self, dialog):
        """
        Obtém os dados de host e porta informados no diálogo de configuração de proxy.

        - Lê os valores digitados nos campos de entrada do diálogo.
        - Remove espaços em branco e caracteres inválidos.
        - Valida se a porta é um número inteiro.
        - Retorna uma tupla (host, port) em caso de sucesso, ou (None, None) em caso de erro.
        """
        host = dialog.host_input.text().strip()
        port_text = dialog.port_input.text().replace('_', '').strip()
        if host and port_text:
            try:
                port = int(port_text)
                return host, port
            except ValueError:
                print(f"Porta inválida: '{port_text}'")
        return None, None

    def definir_proxy_temporario(self, dialog):
        """
        Define um proxy temporário a partir dos dados informados no diálogo.

        - Obtém host e porta via `get_proxy_from_dialog`.
        - Caso válidos, aplica o proxy imediatamente.
        - Fecha o diálogo após a configuração.
        """
        host, port = self.get_proxy_from_dialog(dialog)
        if host and port:
            self.definir_proxy(host, port)
            dialog.close()

    def salvar_e_usar_proxy(self, dialog):
        """
        Salva um novo proxy na lista e o aplica imediatamente.

        - Obtém host e porta do diálogo.
        - Permite atribuir um apelido ao proxy (ou usa host:port como padrão).
        - Adiciona o proxy à lista persistente (`proxy_list`) e salva em arquivo.
        - Define o proxy como ativo e fecha o diálogo.
        """
        host, port = self.get_proxy_from_dialog(dialog)
        if host and port:
            apelido = dialog.apelido_input.text().strip()
            if not apelido:
                apelido = f"{host}:{port}"
            novo_proxy = {"apelido": apelido, "host": host, "port": port}
            self.proxy_list.append(novo_proxy)
            self.salvar_proxies()
            self.definir_proxy(host, port, apelido=apelido)
            dialog.close()

    def trocar_proxy(self):
        """
        Alterna entre os proxies salvos na lista (`proxy_list`).

        - Caso não haja proxies salvos, desativa o proxy e retorna.
        - Incrementa o índice atual (`current_proxy_index`) para rotacionar.
        - Se o índice ultrapassar o limite, volta para -1 (conexão direta).
        - Aplica o próximo proxy da lista ou desativa caso o índice seja -1.
        """
        if not self.proxy_list:
            print("Nenhum proxy salvo para rotacionar.")
            self.desativar_proxy()
            return

        self.current_proxy_index += 1
        if self.current_proxy_index >= len(self.proxy_list):
            self.current_proxy_index = -1

        if self.current_proxy_index == -1:
            self.desativar_proxy()
        else:
            proxy_info = self.proxy_list[self.current_proxy_index]
            self.definir_proxy(proxy_info["host"], proxy_info["port"], apelido=proxy_info["apelido"])

    def definir_proxy(self, host, port, apelido=None):
        """
        Define um proxy HTTP como proxy da aplicação.

        - Cria um objeto `QNetworkProxy` com host e porta informados.
        - Aplica o proxy globalmente na aplicação.
        - Atualiza a barra de status com a informação do proxy ativo.
        """
        proxy = QNetworkProxy(QNetworkProxy.ProxyType.HttpProxy, host, port)
        QNetworkProxy.setApplicationProxy(proxy)

        status_text = apelido if apelido else f"{host}:{port}"
        self.proxy_status_message = f"Proxy Ativo: {status_text}"
        self.status_bar.showMessage(self.proxy_status_message)
        print(self.proxy_status_message)

    def desativar_proxy(self):
        """
        Desativa o uso de proxy, restaurando a conexão direta.

        - Define `QNetworkProxy.NoProxy` como configuração global.
        - Atualiza a barra de status e imprime mensagem no console.
        """
        QNetworkProxy.setApplicationProxy(QNetworkProxy.NoProxy)
        self.proxy_status_message = "Conexão Direta"
        self.status_bar.showMessage(self.proxy_status_message)
        print("Proxy desativado.")