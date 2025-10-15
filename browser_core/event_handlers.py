# browser_core/event_handlers.py

"""
Este módulo contém o EventHandlersMixin, responsável por toda a lógica de
manipulação de eventos (slots) que são emitidos por vários componentes da UI,
principalmente pelo WebView e pelo gestor de abas.
"""

# --- Imports da Biblioteca Padrão ---
import os

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QPainter, QPixmap, QIcon
from PySide6.QtSvg import QSvgRenderer

# --- Imports Locais da Aplicação ---
from components import WebView, HtmlEditor, SplitEditor
# QPlainTextEdit é usado para verificação de tipo.
from PySide6.QtWidgets import QPlainTextEdit


class EventHandlersMixin:
    """
    Mixin que encapsula todos os slots que respondem a sinais de componentes
    da UI, mantendo a classe principal do navegador focada na orquestração.
    """
    
    def aba_alterada(self, index):
        """
        Executa ajustes na interface e nos controles quando a aba ativa é alterada.

        Responsabilidades:
        - Identificar o tipo de widget da aba selecionada:
            - WebView → página web.
            - SplitEditor → editor de código com visualização lado a lado.
            - HtmlEditor → editor de HTML simples.
            - QPlainTextEdit (não editor) → visualização de código-fonte.
        - Habilitar ou desabilitar botões e ações conforme o tipo da aba.
        - Atualizar a barra de URL para refletir o contexto da aba ativa.
        - Atualizar botões de estado (JavaScript, Favorito, Blocker).
        """
        widget = self.tabs.widget(index)

        # Identificação do tipo de aba
        is_webview = isinstance(widget, WebView)
        is_split_editor = isinstance(widget, SplitEditor)
        is_editor = is_split_editor or isinstance(widget, HtmlEditor)
        is_source_view = isinstance(widget, QPlainTextEdit) and not is_editor

        # Habilita ação de salvar apenas em editores
        if hasattr(self, 'save_action'):
            self.save_action.setEnabled(is_editor)

        # Habilita botões de navegação apenas em WebViews
        for btn in [self.btn_voltar, self.btn_avancar, self.btn_recarregar,
                    self.btn_js, self.btn_toggle_favorito, self.btn_blocker]:
            btn.setEnabled(is_webview)

        # Campo de busca habilitado em WebViews, editores e visualização de código-fonte
        self.find_input.setEnabled(is_webview or is_editor or is_source_view)

        # Botão de preview habilitado apenas em SplitEditor
        if hasattr(self, 'btn_preview'):
            self.btn_preview.setEnabled(is_split_editor)

        # Atualiza a barra de URL conforme o tipo de aba
        if is_webview:
            self.atualizar_url_bar(widget.url(), widget)
        elif is_source_view:
            self.url_bar.setText("about:source")
        elif is_editor:
            self.url_bar.setText(f"editor:{self.tabs.tabText(index)}")

        # Atualiza botões de estado
        self.atualizar_botao_js()
        self.atualizar_botao_favorito()
        self.atualizar_botao_blocker()

    def atualizar_icone_aba(self, icon, browser):
        """
        Atualiza o ícone exibido na aba correspondente a um WebView.

        :param icon: Ícone da página carregada.
        :param browser: Instância de WebView associada à aba.
        """
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabIcon(index, icon)


    def inicio_carregamento(self, browser):
        """
        Exibe e reinicia a barra de progresso quando o carregamento de uma página começa.

        - Apenas afeta a aba atualmente ativa.
        """
        if browser == self.aba_atual():
            self.progress_bar.setValue(0)
            self.progress_bar.show()


    def fim_carregamento(self, ok, browser):
        """
        Oculta a barra de progresso quando o carregamento da página termina.

        - Apenas afeta a aba atualmente ativa.
        - O parâmetro `ok` indica se o carregamento foi bem-sucedido.
        """
        if browser == self.aba_atual():
            self.progress_bar.hide()


    def atualizar_progresso(self, progress, browser):
        """
        Atualiza o valor da barra de progresso durante o carregamento da página.

        - Apenas afeta a aba atualmente ativa.
        - O valor `progress` varia de 0 a 100.
        """
        if browser == self.aba_atual():
            self.progress_bar.setValue(progress)
			
    def atualizar_url_bar(self, qurl, browser=None):
        """
        Atualiza a barra de endereços e o indicador de segurança da aba ativa.

        Responsabilidades:
        - Garantir que a atualização só ocorra se o `browser` for a aba atual.
        - Identificar o esquema (protocolo) da URL (`http`, `https`, `gopher`, etc.).
        - Selecionar o ícone, cor e tooltip apropriados com base no protocolo:
            - HTTPS → Cadeado verde (conexão segura).
            - HTTP → Alerta vermelho (conexão não segura).
            - Gopher → Ícone temático (navegação em Gopherspace).
            - Outros → Ícone genérico com indicação do protocolo.
        - Renderizar o ícone SVG colorido e exibi-lo no indicador de segurança.
        - Atualizar o texto da barra de URL com a string completa da URL.
        - Posicionar o cursor no início do campo para facilitar leitura.

        :param qurl: Objeto QUrl representando a URL atual.
        :param browser: Instância de WebView associada à aba (opcional).
        """
        if browser != self.aba_atual():
            return

        icon_size = 16
        scheme = qurl.scheme()

        # Mapeamento de protocolos para ícones, cores e tooltips
        icon_map = {
            'https': ("icons/lock.svg", "green", "Conexão segura (HTTPS)"),
            'http': ("icons/alert-triangle.svg", "red", "Conexão não segura (HTTP)"),
            'gopher': ("icons/rabbit.svg", "#A0522D", "Navegando em Gopherspace"),
        }

        # Seleciona ícone correspondente ou usa padrão
        path, color, tooltip = icon_map.get(
            scheme,
            ("icons/info.svg", "grey", f"Protocolo: {scheme}")
        )

        # Cria ícone SVG colorido e aplica ao indicador de segurança
        icon = self.create_svg_icon(self.get_data_path(path), QColor(color))
        self.security_indicator_label.setPixmap(icon.pixmap(icon_size, icon_size))
        self.security_indicator_label.setToolTip(tooltip)

        # Atualiza a barra de URL
        self.url_bar.setText(qurl.toString())
        self.url_bar.setCursorPosition(0)


    def atualizar_titulo_aba(self, title, browser):
        """
        Atualiza o título exibido na aba correspondente a um WebView.

        Responsabilidades:
        - Localizar o índice da aba associada ao `browser`.
        - Se encontrada, atualizar o texto da aba com o título da página.
        - Limitar o título a 30 caracteres para evitar abas muito largas.

        :param title: Título da página carregada.
        :param browser: Instância de WebView associada à aba.
        """
        index = self.tabs.indexOf(browser)
        if index != -1:
            self.tabs.setTabText(index, title[:30])
	
    def on_link_hovered(self, url):
        """
        Atualiza a barra de status quando o usuário passa o mouse sobre um link.

        Responsabilidades:
        - Exibir a URL do link na barra de status enquanto o mouse estiver sobre ele.
        - Se não houver link (mouse fora de links), exibir a mensagem de status do proxy.

        :param url: URL do link atualmente sob o cursor do mouse.
        """
        self.status_bar.showMessage(url if url else self.proxy_status_message)
		
    def navegar_para_url(self):
        """
        Navega para a URL digitada na barra de endereços.

        Responsabilidades:
        - Ler o texto digitado pelo usuário na barra de URL.
        - Ignorar se o campo estiver vazio.
        - Executar a navegação apenas se a aba atual for um WebView,
          utilizando `_executar_se_webview` para segurança.
        - Delegar o processamento da URL ao método `_processar_navegacao`,
          que trata normalizações (ex.: adicionar http:// se necessário).

        Observação:
        - Esse método é acionado quando o usuário pressiona Enter na barra de endereços.
        """
        url_texto = self.url_bar.text().strip()
        if not url_texto:
            return

        # Executa a navegação na aba atual, se for um WebView
        self._executar_se_webview(lambda aba: self._processar_navegacao(url_texto, aba))
		
    def create_svg_icon(self, icon_path, color):
        """
        Cria um ícone SVG colorido a partir de um arquivo.

        Responsabilidades:
        - Carregar o SVG usando `QSvgRenderer`.
        - Renderizar em um `QPixmap` transparente.
        - Aplicar a cor desejada usando `QPainter` e modo de composição.
        - Retornar o ícone (`QIcon`) pronto para uso em botões ou menus.

        :param icon_path: Caminho para o arquivo SVG.
        :param color: Cor a ser aplicada ao ícone.
        :return: Objeto QIcon com o SVG renderizado e colorido.
        """
        renderer = QSvgRenderer(icon_path)
        pixmap = QPixmap(renderer.defaultSize())
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), color)
        painter.end()

        return QIcon(pixmap)

    def _processar_navegacao(self, url_texto, aba):
        """
        Lida com a lógica de navegação para diferentes tipos de URL.

        Responsabilidades:
        - Identificar o tipo de entrada fornecida pelo usuário (protocolo, arquivo local ou URL web).
        - Se for protocolo Gopher, delega o tratamento para `handle_gopher_request`.
        - Se for um caminho de arquivo local existente, abre-o diretamente no WebView.
        - Caso contrário, assume que é uma URL web:
            - Adiciona "https://" se não houver protocolo explícito.
            - Se a URL terminar em ".pdf", abre em uma nova aba com rótulo "Visualizador PDF".
            - Caso contrário, carrega a URL normalmente na aba atual.

        :param url_texto: Texto digitado pelo usuário (endereço ou caminho).
        :param aba: Instância de WebView onde a navegação será executada.
        """
        if url_texto.startswith("gopher://"):
            # Tratamento especial para protocolo Gopher
            self.handle_gopher_request(url_texto, aba)
        elif os.path.exists(url_texto):
            # Se for um arquivo local existente, abre diretamente
            aba.setUrl(QUrl.fromLocalFile(url_texto))
        else:
            # Se não houver protocolo, assume HTTPS por padrão
            if not (url_texto.startswith("http://") or url_texto.startswith("https://")):
                url_texto = "https://" + url_texto

            url = QUrl(url_texto)

            # Se for PDF, abre em uma nova aba dedicada
            if url.toString().lower().endswith(".pdf"):
                self.adicionar_nova_aba(url, "Visualizador PDF")
            else:
                # Caso contrário, navega normalmente
                aba.setUrl(url)
