# Arquivo: actions.py

import os
import json
import datetime
import requests
import socket
import base64 
import google.generativeai as genai
from PySide6.QtCore import QObject, Signal, QThread
from pathlib import Path
from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import QFileDialog, QPushButton, QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QLineEdit, QInputDialog, QMessageBox
from PySide6.QtGui import QAction, QKeySequence, QTextDocument, QActionGroup
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineDownloadRequest

from dialogs import ProxyDialog, TamperDialog
from components import WebView, HtmlEditor, QPlainTextEdit, UrlInterceptor, SplitEditor

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
            
class FindActions:
    """
    Classe responsável pelas ações de busca de texto no navegador/editor.

    Permite abrir/fechar a barra de busca, localizar texto na aba atual
    (seja em páginas web ou editores de texto) e navegar entre as ocorrências.
    """

    def abrir_busca(self):
        """
        Exibe a barra de busca e coloca o foco no campo de entrada.

        - Torna a barra de busca visível.
        - Garante que o usuário possa digitar imediatamente o termo a ser buscado.
        """
        self.find_toolbar.show()
        self.find_input.setFocus()

    def fechar_busca(self):
        """
        Fecha a barra de busca e limpa os destaques de pesquisa.

        - Oculta a barra de busca.
        - Se a aba atual for uma WebView, limpa os resultados da busca.
        - Se for um editor de texto (HtmlEditor ou QPlainTextEdit),
          remove a seleção atual do cursor.
        """
        self.find_toolbar.hide()
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            aba.findText("")  # limpa destaques
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            cursor = aba.textCursor()
            cursor.clearSelection()
            aba.setTextCursor(cursor)

    def buscar_texto(self, text):
        """
        Realiza a busca inicial do texto informado na aba atual.

        - Em WebView: usa o método `findText` do QWebEnginePage.
        - Em editores de texto: posiciona o cursor no início do documento
          e executa a busca pelo termo.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            aba.findText(text)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            cursor = aba.textCursor()
            cursor.setPosition(0)  # início do documento
            aba.setTextCursor(cursor)
            aba.find(text)

    def buscar_proximo(self):
        """
        Busca a próxima ocorrência do termo digitado.

        - Obtém o texto do campo de busca.
        - Em WebView: chama `findText` novamente para avançar.
        - Em editores de texto: usa `find` para localizar a próxima ocorrência.
        """
        aba = self.aba_atual()
        text = self.find_input.text()
        if isinstance(aba, WebView):
            aba.findText(text)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            aba.find(text)

    def buscar_anterior(self):
        """
        Busca a ocorrência anterior do termo digitado.

        - Obtém o texto do campo de busca.
        - Em WebView: usa a flag `FindBackward` do QWebEnginePage.
        - Em editores de texto: usa a flag `FindBackward` do QTextDocument.
        """
        aba = self.aba_atual()
        text = self.find_input.text()
        if isinstance(aba, WebView):
            aba.findText(text, QWebEnginePage.FindFlag.FindBackward)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            aba.find(text, QTextDocument.FindFlag.FindBackward)
        

class PrivacyActions:
    """
    Classe responsável pelas ações de privacidade do navegador.

    Inclui:
    - Carregamento de listas de bloqueio de domínios.
    - Ativação/desativação do bloqueador de conteúdo.
    - Controle da execução de JavaScript.
    - Atualização dos botões de interface relacionados à privacidade.
    """

    def carregar_blocklist(self):
        """
        Carrega a lista de domínios bloqueados a partir de um arquivo JSON.

        - O arquivo esperado é 'blocklist.json'.
        - Caso o arquivo exista, os domínios são carregados em um conjunto (set).
        - Caso não exista, inicializa a lista como vazia.
        - Exibe mensagens de log informativas ou de aviso.
        """
        try:
            with open("blocklist.json", "r") as f:
                self.blocklist = set(json.load(f))
                print(f"[INFO] Lista de bloqueio carregada com {len(self.blocklist)} domínios.")
        except FileNotFoundError:
            print("[AVISO] Arquivo 'blocklist.json' não encontrado.")
            self.blocklist = set()

    def toggle_blocker(self, checked):
        """
        Ativa ou desativa o bloqueador de conteúdo na aba atual.

        - Verifica se a aba atual é uma WebView e possui um interceptor configurado.
        - Define o estado do bloqueador (ativo/inativo) com base no parâmetro `checked`.
        - Atualiza o botão de interface correspondente.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView) and hasattr(aba.page().profile(), 'interceptor'):
            aba.page().profile().interceptor.blocking_enabled = checked
            print(f"Bloqueador {'ativado' if checked else 'desativado'} para a aba atual.")
        self.atualizar_botao_blocker()

    def atualizar_botao_blocker(self):
        """
        Atualiza o estado visual do botão de bloqueio de conteúdo.

        - Se a aba atual for uma WebView com interceptor:
            - Habilita o botão.
            - Ajusta o texto, cor e estado (ON/OFF) conforme o bloqueador esteja ativo ou não.
        - Caso contrário:
            - Desabilita o botão e restaura estilo padrão.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView) and hasattr(aba.page().profile(), 'interceptor'):
            self.btn_blocker.setEnabled(True)
            blocker_ativo = aba.page().profile().interceptor.blocking_enabled
            if blocker_ativo:
                self.btn_blocker.setText("Block ON")
                self.btn_blocker.setStyleSheet("background-color: lightcoral; color: white;")
                self.btn_blocker.setChecked(True)
            else:
                self.btn_blocker.setText("Block OFF")
                self.btn_blocker.setStyleSheet("background-color: lightgreen; color: black;")
                self.btn_blocker.setChecked(False)
        else:
            self.btn_blocker.setText("Block")
            self.btn_blocker.setStyleSheet("")
            self.btn_blocker.setEnabled(False)

    def toggle_javascript(self, checked):
        """
        Ativa ou desativa a execução de JavaScript na aba atual.

        - Se a aba atual for uma WebView, altera o atributo `JavascriptEnabled`.
        - O parâmetro `checked` representa o estado do botão (ativado/desativado).
        - Após a alteração, atualiza o botão de interface correspondente.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            aba.page().settings().setAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled,
                not checked
            )
        self.atualizar_botao_js()

    def atualizar_botao_js(self):
        """
        Atualiza o estado visual do botão de controle de JavaScript.

        - Se a aba atual for uma WebView:
            - Habilita o botão.
            - Ajusta o texto, cor e estado (ON/OFF) conforme o JavaScript esteja habilitado ou não.
        - Caso contrário:
            - Desabilita o botão e restaura estilo padrão.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            self.btn_js.setEnabled(True)
            js_habilitado = aba.page().settings().testAttribute(
                QWebEngineSettings.WebAttribute.JavascriptEnabled
            )
            if js_habilitado:
                self.btn_js.setText("JS ON")
                self.btn_js.setStyleSheet("background-color: lightgreen; color: black;")
                self.btn_js.setChecked(False)
            else:
                self.btn_js.setText("JS OFF")
                self.btn_js.setStyleSheet("background-color: lightcoral; color: white;")
                self.btn_js.setChecked(True)
        else:
            self.btn_js.setText("JS")
            self.btn_js.setStyleSheet("")
            self.btn_js.setEnabled(False)
            
class DownloadActions:
    """
    Mixin que implementa as ações relacionadas a downloads de arquivos no navegador.

    Responsabilidades:
    - Interceptar solicitações de download.
    - Permitir ao usuário escolher o local de salvamento.
    - Monitorar o progresso do download.
    - Exibir mensagens de status e notificar conclusão, cancelamento ou falha.
    """

    def handle_download_request(self, download: QWebEngineDownloadRequest):
        """
        Manipula uma nova solicitação de download.

        - Sugere o diretório padrão de downloads do usuário.
        - Abre um diálogo para que o usuário escolha onde salvar o arquivo.
        - Caso o usuário confirme:
            - Define o diretório e nome do arquivo no objeto `download`.
            - Conecta sinais para monitorar progresso e estado final.
            - Exibe mensagem de status e inicia o download.
            - Adiciona o download à lista de downloads ativos.
        - Caso o usuário cancele:
            - Cancela o download e exibe mensagem no console.
        """
        suggested_path = os.path.join(str(Path.home()), "Downloads", download.downloadFileName())
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", suggested_path)

        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))

            # Conecta sinais para progresso e término
            download.receivedBytesChanged.connect(lambda: self.update_download_progress(download))
            download.stateChanged.connect(lambda state, download=download: self.finish_download(state, download))

            self.status_bar.showMessage(f"Baixando {os.path.basename(file_path)}...")
            download.accept()
            self.active_downloads.append(download)
        else:
            print("Download cancelado.")
            download.cancel()

    def update_download_progress(self, download: QWebEngineDownloadRequest):
        """
        Atualiza o progresso do download em tempo real.

        - Obtém bytes recebidos e total esperado.
        - Se o total for conhecido, calcula a porcentagem concluída.
        - Caso contrário, exibe apenas o tamanho já baixado em KB.
        - Atualiza a barra de status com a informação.
        """
        bytes_received = download.receivedBytes()
        bytes_total = download.totalBytes()
        if bytes_total > 0:
            percent = int((bytes_received / bytes_total) * 100)
            self.status_bar.showMessage(f"Baixando... {percent}%")
        else:
            self.status_bar.showMessage(f"Baixando... {bytes_received / 1024:.0f} KB")

    def finish_download(self, state, download: QWebEngineDownloadRequest):
        """
        Trata o término de um download, exibindo mensagens adequadas.

        - Se concluído com sucesso: mostra mensagem de "Download concluído".
        - Se cancelado: mostra mensagem de "Download cancelado".
        - Se interrompido/falhou: mostra mensagem de erro.
        - Remove o download da lista de downloads ativos.
        """
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            self.status_bar.showMessage("Download concluído!", 5000)
        elif state == QWebEngineDownloadRequest.DownloadCancelled:
            self.status_bar.showMessage("Download cancelado.", 5000)
        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            self.status_bar.showMessage("Download interrompido/falhou.", 5000)

        if download in self.active_downloads:
            self.active_downloads.remove(download)
            
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
            
class DevToolsActions:
    """
    Mixin para as Ferramentas de Desenvolvedor (DevTools).

    Responsabilidades:
    - Exibir ou ocultar o painel de rede (network panel).
    - Abrir o diálogo de interceptação e modificação de requisições (TamperDialog).
    """

    def toggle_network_panel(self):
        """
        Alterna a visibilidade do painel de rede (network_dock).

        - Se o painel já estiver visível, oculta.
        - Caso contrário, exibe.
        - Útil para desenvolvedores inspecionarem requisições e respostas HTTP.
        """
        if self.network_dock.isVisible():
            self.network_dock.hide()
        else:
            self.network_dock.show()

    def abrir_dialogo_tamper(self, request_info):
        """
        Abre o diálogo de interceptação e modificação de requisições (TamperDialog).

        - Recebe informações da requisição (`request_info`).
        - Cria uma instância de `TamperDialog` passando os dados e a referência da janela principal.
        - Mantém a referência em `self.tamper_dialog` para evitar que o diálogo seja destruído pelo garbage collector.
        - Exibe o diálogo para que o usuário possa inspecionar ou alterar a requisição antes do envio.
        """
        self.tamper_dialog = TamperDialog(request_info, self)
        self.tamper_dialog.show()   # mantém referência em self
        
class ProtocolActions:
    """
    Mixin para lidar com protocolos alternativos, como o Gopher.

    Responsabilidades:
    - Interpretar e processar requisições Gopher.
    - Converter respostas em HTML para exibição no navegador.
    - Suportar diferentes tipos de conteúdo (texto, menus, imagens).
    """

    def handle_gopher_request(self, url, tab):
        """
        Manipula uma requisição Gopher e renderiza o resultado na aba especificada.

        - Analisa a URL para extrair host, porta, seletor e tipo de conteúdo.
        - Estabelece conexão TCP com o servidor Gopher.
        - Envia o seletor e recebe a resposta bruta.
        - Se o tipo for imagem (g, I, p), converte os dados em HTML com <img>.
        - Caso contrário, interpreta o mapa Gopher (menus/texto) e converte em HTML.
        - Em caso de erro, exibe mensagem de falha na aba.
        """
        try:
            # Extrai tipo de conteúdo da query string, se presente
            gopher_type = None
            if "?gopher_type=" in url:
                url_parts = url.split("?gopher_type=")
                url = url_parts[0]
                gopher_type = url_parts[1]

            # Extrai host, porta e seletor da URL
            parts = url.split("//")[1].split("/")
            host_port = parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 70
            selector = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""

            # Conexão TCP com servidor Gopher
            with socket.create_connection((host, port), timeout=10) as s:
                s.sendall((selector + "\r\n").encode('utf-8'))
                response_data = b""
                while True:
                    chunk = s.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk

            # Decide como processar a resposta
            if gopher_type in ('g', 'I', 'p'):
                # Conteúdo de imagem → gera HTML com <img>
                html = self._parse_image_to_html(response_data, gopher_type)
            else:
                # Conteúdo textual/menu → converte mapa Gopher em HTML
                gopher_map = response_data.decode('utf-8', errors='ignore')
                html = self._parse_gopher_map_to_html(gopher_map, host, port)

            tab.setHtml(html, QUrl(url))

        except Exception as e:
            print(f"Erro ao acessar Gopher: {e}")
            tab.setHtml(f"<h1>Erro ao acessar Gopher</h1><p>{e}</p>")

    def _parse_image_to_html(self, image_data, gopher_type):
        """
        Converte dados brutos de imagem em uma página HTML com a imagem embutida.

        - Suporta GIF (g), JPEG (I) e PNG (p).
        - Codifica os bytes da imagem em Base64.
        - Retorna HTML com <img> centralizado e fundo escuro.
        """
        mime_map = {'g': 'image/gif', 'p': 'image/png', 'I': 'image/jpeg'}
        mime_type = mime_map.get(gopher_type, 'application/octet-stream')

        b64_data = base64.b64encode(image_data).decode('ascii')

        return (
            f'<html><body style="background-color: #333; display: grid; '
            f'place-items: center; margin: 0;">'
            f'<img src="data:{mime_type};base64,{b64_data}"></body></html>'
        )

    def _parse_gopher_map_to_html(self, gopher_map, current_host, current_port):
        """
        Converte um mapa Gopher (texto estruturado) em HTML navegável.

        - Cada linha do mapa representa um item (arquivo, diretório, link, etc.).
        - Interpreta o tipo do item (primeiro caractere da linha).
        - Gera links HTML apropriados para cada tipo:
            - '0' → Documento de texto
            - '1' → Diretório
            - 'h' → Link externo (HTTP/HTML)
            - 'g', 'I', 'p' → Imagens
            - 'i' → Informação (texto simples)
            - Outros → Exibe como desconhecido
        - Retorna HTML estilizado com <pre> e ícones visuais.
        """
        html_lines = [
            '<html><head><meta charset="UTF-8">',
            '<title>Gopher Page</title>',
            '<style>body { font-family: monospace; background-color: #f0f0f0; '
            'color: #333; } a { text-decoration: none; color: #0000FF;} '
            'p { margin: 2px; }</style>',
            '</head><body><h2>Gopherspace</h2><pre>'
        ]

        for line in gopher_map.splitlines():
            if not line or len(line) < 2:
                continue

            item_type = line[0]
            parts = line[1:].split('\t')
            display_text = parts[0]
            selector = parts[1] if len(parts) > 1 else ""
            host = parts[2] if len(parts) > 2 else current_host
            port = parts[3] if len(parts) > 3 else current_port

            if item_type == 'i':
                html_lines.append(f'<p>  {display_text}</p>')
            elif item_type == '0':
                html_lines.append(
                    f'<p>📄 <a href="gopher://{host}:{port}{selector}?gopher_type=0">'
                    f'{display_text}</a></p>'
                )
            elif item_type == '1':
                html_lines.append(
                    f'<p>📁 <a href="gopher://{host}:{port}{selector}?gopher_type=1">'
                    f'{display_text}</a></p>'
                )
            elif item_type == 'h':
                html_url = selector.replace("URL:", "")
                html_lines.append(f'<p>🌐 <a href="{html_url}">{display_text}</a></p>')
            elif item_type in ('g', 'I', 'p'):  # GIF, JPEG, PNG
                html_lines.append(
                    f'<p>🖼️ <a href="gopher://{host}:{port}{selector}?gopher_type={item_type}">'
                    f'{display_text}</a></p>'
                )
            else:
                html_lines.append(
                    f'<p>❓ <a href="gopher://{host}:{port}{selector}?gopher_type={item_type}">'
                    f'{display_text}</a> (Tipo {item_type})</p>'
                )

        html_lines.append('</pre></body></html>')
        return "".join(html_lines)
        
class WorkerIA(QObject):
    """
    Worker responsável por executar chamadas à API de IA em uma thread separada.

    Responsabilidades:
    - Configurar e chamar o modelo de IA (Gemini).
    - Emitir sinais com o resultado, erro ou término da execução.
    - Garantir que a interface gráfica (UI) permaneça responsiva durante a chamada.
    """

    # --- Sinais Qt ---
    resultado_pronto = Signal(str)   # Emitido quando a resposta da IA está disponível
    erro_ocorrido = Signal(str)      # Emitido em caso de erro na chamada da API
    finished = Signal()              # Emitido quando a execução é concluída (com ou sem sucesso)

    def __init__(self, api_key, prompt):
        """
        Inicializa o worker com a chave da API e o prompt a ser enviado.

        :param api_key: Chave de autenticação para a API do Gemini.
        :param prompt: Texto de entrada (instrução ou pergunta) a ser enviado ao modelo.
        """
        super().__init__()
        self.api_key = api_key
        self.prompt = prompt

    def rodar(self):
        """
        Executa a chamada à API do Gemini em uma thread separada.

        - Configura a biblioteca `genai` com a chave da API.
        - Cria uma instância do modelo `gemini-2.5-flash`.
        - Envia o prompt e aguarda a resposta.
        - Emite o sinal `resultado_pronto` com o texto retornado.
        - Em caso de erro, emite `erro_ocorrido` com a mensagem de exceção.
        - Sempre emite `finished` ao final, garantindo que a thread seja liberada.
        """
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(self.prompt)

            # Emite o resultado para ser tratado pela UI
            self.resultado_pronto.emit(response.text)

        except Exception as e:
            # Emite erro para ser exibido/logado pela aplicação
            self.erro_ocorrido.emit(f"Erro na API do Gemini: {e}")

        finally:
            # Garante que a thread seja finalizada corretamente
            self.finished.emit()

class AIActions:
    """
    Mixin para as ações de Inteligência Artificial.

    Responsabilidades:
    - Gerenciar a chave de API do Gemini (solicitar ao usuário, salvar e reutilizar).
    - Criar e iniciar threads para execução de prompts de IA sem travar a interface.
    - Integrar os resultados da IA ao painel de assistente (ai_panel).
    """

    def processar_prompt_ia(self, prompt):
        """
        Processa um prompt de IA fornecido pelo usuário.

        Fluxo:
        1. Verifica se a chave de API está configurada.
           - Caso não esteja, solicita ao usuário via diálogo.
           - Se o usuário fornecer, salva a chave para uso futuro.
           - Se não fornecer, cancela a operação e informa no painel de IA.
        2. Se a chave estiver disponível, cria uma thread dedicada.
        3. Instancia um WorkerIA com a chave e o prompt.
        4. Conecta sinais do worker para:
            - Exibir resposta no painel de IA.
            - Exibir erros no painel de IA.
            - Encerrar e limpar a thread ao término.
        5. Inicia a execução da thread.
        """
        if not self.api_key:
            texto, ok = QInputDialog.getText(
                self,
                "Chave de API do Gemini",
                "Por favor, insira sua chave de API do Google AI Studio:"
            )
            if ok and texto:
                self.api_key = texto.strip()
                self.salvar_config()  # Persiste a chave para próximas execuções
            else:
                self.ai_panel.set_response(
                    "Operação cancelada. A chave de API é necessária para usar o assistente."
                )
                return

        if not self.api_key:
            return

        # Criação da thread e do worker
        self.thread = QThread()
        self.worker = WorkerIA(self.api_key, prompt)
        self.worker.moveToThread(self.thread)

        # Conexão de sinais
        self.thread.started.connect(self.worker.rodar)
        self.worker.resultado_pronto.connect(self.ai_panel.set_response)
        self.worker.erro_ocorrido.connect(self.ai_panel.set_response)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Inicia a thread
        self.thread.start()

    def _iniciar_worker_ia_com_contexto(self, page_text, original_prompt):
        """
        Cria o prompt final com base no contexto da página e inicia o worker de IA.

        - Recebe o texto da página e o prompt original do usuário.
        - Se houver texto da página:
            - Limita o conteúdo a 15.000 caracteres (para evitar excesso de dados).
            - Constrói um prompt contextualizado, instruindo a IA a responder
              exclusivamente com base no conteúdo fornecido.
        - Cria e inicia uma thread com WorkerIA, de forma idêntica ao método anterior.
        """
        final_prompt = original_prompt

        if page_text:
            page_text = page_text[:15000]  # Limita tamanho do contexto
            final_prompt = f"""Com base EXCLUSIVAMENTE no seguinte texto de uma página da web:

'''
{page_text}
'''

Responda ao seguinte pedido do usuário: "{original_prompt}"
"""

        # Criação da thread e do worker com prompt contextualizado
        self.thread = QThread()
        self.worker = WorkerIA(self.api_key, final_prompt)
        self.worker.moveToThread(self.thread)

        # Conexão de sinais
        self.thread.started.connect(self.worker.rodar)
        self.worker.resultado_pronto.connect(self.ai_panel.set_response)
        self.worker.erro_ocorrido.connect(self.ai_panel.set_response)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Inicia a thread
        self.thread.start()