# browser_core/tab_manager.py

"""
Este módulo contém o TabManagerMixin, responsável por toda a lógica de
gestão de abas (tabs) no navegador.

Isto inclui a criação de novas abas (tanto de navegação quanto de edição),
fecho, seleção e a obtenção da aba atualmente ativa.
"""

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage, QWebEngineSettings

# --- Imports Locais da Aplicação ---
from components import WebView, HtmlEditor, SplitEditor, UrlInterceptor


class TabManagerMixin:
    """
    Mixin que encapsula a lógica de criação e gestão de abas.
    """

    def _criar_nova_aba_webview(self, label):
        """
        Cria e configura uma nova instância de WebView para uma aba.

        Responsabilidades:
        - Instanciar um novo WebView com seu próprio perfil e página.
        - Configurar o User-Agent inicial.
        - Conectar sinais de eventos de navegação, carregamento e histórico.
        - Integrar com o painel de rede e interceptador de requisições.
        - Habilitar recursos adicionais (plugins e visualizador de PDF).
        - Adicionar a nova aba ao conjunto de abas do navegador.

        :param label: Texto exibido na aba (ex.: "Nova Aba").
        :return: Instância configurada de WebView.
        """
        # Cria o WebView e associa um perfil/página
        browser = WebView()
        profile = QWebEngineProfile(browser)
        page = QWebEnginePage(profile, browser)
        browser.setPage(page)

        # Define o User-Agent inicial como o padrão do navegador
        page.profile().setHttpUserAgent(QWebEngineProfile.defaultProfile().httpUserAgent())

        # --- Conexão de sinais de eventos ---
        page.linkHovered.connect(self.on_link_hovered)  # Hover em links
        browser.new_tab_requested.connect(self.adicionar_nova_aba)  # Solicitação de nova aba
        browser.editor_requested.connect(self.abrir_editor_html)  # Abrir editor de código
        browser.network_panel_toggled.connect(self.toggle_network_panel)  # Alternar painel de rede
        browser.history_requested.connect(self.abrir_aba_historico)  # Abrir histórico

        # Atualizações visuais e de estado da aba
        browser.iconChanged.connect(lambda icon, b=browser: self.atualizar_icone_aba(icon, b))
        browser.loadProgress.connect(lambda p, b=browser: self.atualizar_progresso(p, b))
        browser.loadStarted.connect(lambda b=browser: self.inicio_carregamento(b))
        browser.loadFinished.connect(lambda ok, b=browser: self.fim_carregamento(ok, b))
        browser.urlChanged.connect(lambda qurl, b=browser: self.atualizar_url_bar(qurl, b))
        browser.titleChanged.connect(lambda t, b=browser: self.atualizar_titulo_aba(t, b))
        browser.urlChanged.connect(self.atualizar_botao_favorito)  # Atualiza botão de favoritos
        browser.codigoFonteDisponivel.connect(self.abrir_aba_codigo_fonte)  # Exibir código-fonte

        # Conecta eventos de download ao manipulador customizado
        profile.downloadRequested.connect(self.handle_download_request)

        # --- Interceptor de requisições (para bloqueio e painel de rede) ---
        interceptor = UrlInterceptor(self.blocklist, self)
        interceptor.requestIntercepted.connect(self.network_panel.add_request)
        profile.setUrlRequestInterceptor(interceptor)
        profile.interceptor = interceptor  # Mantém referência no perfil

        # --- Configurações adicionais ---
        browser.settings().setAttribute(QWebEngineSettings.PluginsEnabled, True)
        if hasattr(QWebEngineSettings.WebAttribute, "PdfViewerEnabled"):
            browser.settings().setAttribute(QWebEngineSettings.WebAttribute.PdfViewerEnabled, True)

        # --- Adiciona a aba ao conjunto de abas ---
        index = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(index)

        return browser
		
    def adicionar_nova_aba(self, url=None, label="Nova Aba"):
        """
        Cria e adiciona uma nova aba ao navegador.

        Responsabilidades:
        - Criar uma nova instância de WebView configurada via `_criar_nova_aba_webview`.
        - Conectar o evento de carregamento finalizado (`loadFinished`) para registrar
          a página no histórico de navegação.
        - Definir a URL inicial da aba:
            - Se nenhuma URL for fornecida, abre "about:blank".
            - Se a URL usar o protocolo Gopher, delega o tratamento a `handle_gopher_request`.
            - Caso contrário, carrega a URL normalmente no WebView.

        :param url: (opcional) URL inicial a ser carregada na nova aba.
        :param label: Texto exibido na aba (padrão: "Nova Aba").
        """
        # Define a URL inicial (ou "about:blank" se não houver)
        url_obj = url if url is not None else QUrl("about:blank")

        # Cria a aba com WebView configurado
        browser = self._criar_nova_aba_webview(label)

        # Conecta o evento de carregamento para salvar no histórico
        browser.loadFinished.connect(lambda ok, b=browser: self.adicionar_ao_historico(b))

        # Tratamento especial para protocolo Gopher
        if url_obj.scheme() == 'gopher':
            self.handle_gopher_request(url_obj.toString(), browser)
        else:
            browser.setUrl(url_obj)
			
    def aba_atual(self):
        """
        Retorna o widget da aba atualmente ativa.

        :return: Widget da aba selecionada (pode ser WebView, Editor, etc.).
        """
        return self.tabs.currentWidget()


    def fechar_aba(self, index):
        """
        Fecha a aba no índice especificado.

        Responsabilidades:
        - Garante que sempre exista pelo menos uma aba aberta (não fecha se houver apenas uma).
        - Obtém o widget da aba e o deleta corretamente.
        - Remove a aba da interface.

        :param index: Índice da aba a ser fechada.
        """
        if self.tabs.count() < 2:
            return
        widget = self.tabs.widget(index)
        if widget:
            widget.deleteLater()
        self.tabs.removeTab(index)
		
    def select_next_tab(self):
        """
        Seleciona a próxima aba no conjunto de abas.

        - Se houver abas abertas, move o índice atual para a próxima aba.
        - Utiliza aritmética modular (%) para circular entre as abas.
        """
        count = self.tabs.count()
        if count > 0:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() + 1) % count)


    def select_previous_tab(self):
        """
        Seleciona a aba anterior no conjunto de abas.

        - Se houver abas abertas, move o índice atual para a aba anterior.
        - Utiliza aritmética modular (%) para circular entre as abas.
        """
        count = self.tabs.count()
        if count > 0:
            self.tabs.setCurrentIndex((self.tabs.currentIndex() - 1 + count) % count)
			
    def abrir_editor_html(self, content="", title="Editor"):
        """
        Abre uma nova aba com o editor de HTML.

        Responsabilidades:
        - Cria uma instância de `SplitEditor`.
        - Define o conteúdo inicial do editor (se fornecido).
        - Adiciona a aba com o título especificado.
        - Define a aba recém-criada como ativa.

        :param content: Conteúdo inicial a ser exibido no editor.
        :param title: Título da aba (padrão: "Editor").
        """
        editor_widget = SplitEditor(self)
        editor_widget.editor.setPlainText(content)
        index = self.tabs.addTab(editor_widget, title)
        self.tabs.setCurrentIndex(index)


    def abrir_aba_codigo_fonte(self, html):
        """
        Abre uma nova aba exibindo o código-fonte em modo somente leitura.

        Responsabilidades:
        - Cria uma instância de `HtmlEditor`.
        - Define o conteúdo HTML fornecido.
        - Torna o editor somente leitura.
        - Adiciona a aba com o título "Código-Fonte".
        - Define a aba recém-criada como ativa.

        :param html: Código HTML a ser exibido.
        """
        editor = HtmlEditor()
        editor.setPlainText(html)
        editor.setReadOnly(True)
        index = self.tabs.addTab(editor, "Código-Fonte")
        self.tabs.setCurrentIndex(index)

    def ver_codigo_fonte_aba_atual(self):
        """
        Exibe o código-fonte da aba atual.

        - Executa a ação `ver_codigo_fonte()` apenas se a aba atual for um WebView.
        - Utiliza `_executar_se_webview` para garantir segurança.
        """
        self._executar_se_webview(lambda aba: aba.ver_codigo_fonte())
	
    def abrir_editor_split(self):
        """
        Abre uma nova aba com o editor de código em modo "lado a lado".

        Responsabilidades:
        - Cria uma instância de `SplitEditor`.
        - Adiciona como uma nova aba com o rótulo "Editor Lado a Lado".
        - Define a aba recém-criada como a aba ativa.
        """
        index = self.tabs.addTab(SplitEditor(self), "Editor Lado a Lado")
        self.tabs.setCurrentIndex(index)