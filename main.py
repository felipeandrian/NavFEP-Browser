# Arquivo: main.py

import sys
import os
import json
from pathlib import Path

# --- CORREÇÃO DE PLATAFORMA PARA LINUX ---
if sys.platform == "linux":
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

from PySide6.QtCore import QUrl, QLocale, Signal, Qt, QLibraryInfo, QTranslator
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QToolBar,
    QTabWidget, QMenu, QPlainTextEdit, QFileDialog, QProgressBar, QDockWidget, QWidget, QHBoxLayout, QLabel, QToolButton, QStyle
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut, QTextDocument, QIcon, QActionGroup, QColor, QPixmap, QPainter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings, QWebEngineProfile

# Módulos do projeto
from panels import AIPanel
from components import WebView, HtmlEditor, UrlInterceptor, NetworkPanel, SplitEditor
from actions import FileMenuActions, BookmarkActions, FindActions, PrivacyActions, DownloadActions, HistoryActions, DevToolsActions, ProtocolActions, AIActions

# --- CONSTANTES GLOBAIS ---
# Nomes de arquivos de configuração e dados
CONFIG_FILE_NAME = "navfep_config.json"
HISTORY_FILE_NAME = "navfep_history.json"
PROXIES_FILE = "proxies.json"
BOOKMARKS_FILE = "bookmarks.json"

# URLs e Títulos Padrão
PAGINA_INICIAL_URL = "https://f3l1p3.neocities.org"
PAGINA_INICIAL_TITULO = "Página Inicial"

# --- FUNÇÕES AUXILIARES ---
def get_data_path(filename):
    """Retorna o caminho completo para um arquivo de dados, funcionando tanto em modo script quanto em executável (PyInstaller)."""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)

def carregar_traducoes(app):
    """Carrega os arquivos de tradução do Qt para Português."""
    caminho_traducoes = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    qt_translator = QTranslator(app)
    webengine_translator = QTranslator(app)
    if qt_translator.load("qt_pt", caminho_traducoes):
        app.installTranslator(qt_translator)
    if webengine_translator.load("qtwebengine_pt", caminho_traducoes):
        app.installTranslator(webengine_translator)
		
# --- CLASSE PRINCIPAL ---
class Navegador(QMainWindow, FileMenuActions, BookmarkActions, FindActions, PrivacyActions, DownloadActions, HistoryActions, DevToolsActions, ProtocolActions, AIActions):
    """
    Classe principal do navegador, que integra todos os componentes da UI e funcionalidades.
    """
    def __init__(self):
        super().__init__()

        self._configurar_janela()
        self._inicializar_variaveis_e_dados()
        self._setup_ui()
        self._carregar_dados_iniciais()

        # Inicia o navegador com a página inicial
        self.adicionar_nova_aba(QUrl(PAGINA_INICIAL_URL), PAGINA_INICIAL_TITULO)
        
    # --------------------------------------------------------------------------
    # --- MÉTODOS DE INICIALIZAÇÃO (SETUP) ---
    # --------------------------------------------------------------------------

    def _configurar_janela(self):
        """Define as propriedades básicas da janela principal (título, tamanho, ícone)."""
        self.setWindowTitle("Navegador do FEP")
        self.setGeometry(100, 100, 1280, 800)
        icon_path = get_data_path("navfep.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

    def _inicializar_variaveis_e_dados(self):
        """Inicializa as variáveis de estado e estruturas de dados do navegador."""
        self.default_user_agent = QWebEngineProfile.defaultProfile().httpUserAgent()
        self.user_agents = {
            "Chrome no Windows 11": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Edge no Windows 11": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0",
            "Firefox no Windows 11": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Chrome no macOS (Apple Silicon)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Safari no macOS (Apple Silicon)": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Safari/605.1.15",
            "Chrome no Android (Pixel 8)": "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Mobile Safari/537.36",
            "Safari no iPhone (iOS 18)": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1",
            "Chrome no Linux (Ubuntu)": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
            "Firefox no Linux (Ubuntu)": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
            "Googlebot (Robô do Google)": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
        }
        self.current_ua_name = "UA Padrão"
        
        self.api_key = ""
        self.config_file = os.path.join(str(Path.home()), CONFIG_FILE_NAME)
        
        self.proxy_list = []
        self.current_proxy_index = -1
        self.proxies_file = PROXIES_FILE
        self.bookmarks = {}
        self.bookmarks_file = BOOKMARKS_FILE
        self.blocklist = set()
        self.active_downloads = []
        self.history = []
        self.history_file = os.path.join(str(Path.home()), HISTORY_FILE_NAME)

    def _setup_ui(self):
        """Cria e organiza todos os widgets da interface do utilizador."""
        self._criar_sistema_abas()
        self._criar_barra_status()
        self._criar_barra_navegacao()
        self._criar_barra_favoritos()
        self._criar_barra_busca()
        self._criar_paineis()
        self.criar_menus()
        self.setup_shortcuts()

    def _criar_sistema_abas(self):
        """Cria o QTabWidget central para gerenciar as abas."""
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.fechar_aba)
        self.tabs.currentChanged.connect(self.aba_alterada)
        self.setCentralWidget(self.tabs)

    def _criar_barra_status(self):
        """Cria a barra de status e a barra de progresso."""
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumHeight(3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: none; background-color: transparent; } QProgressBar::chunk { background-color: #3498db; }")
        
        self.status_bar = self.statusBar()
        self.status_bar.addPermanentWidget(self.progress_bar, 1)
        self.progress_bar.hide()
        
        self.proxy_status_message = "Conexão Direta"
        self.status_bar.showMessage(self.proxy_status_message)

    def _criar_barra_navegacao(self):
        """
        Cria a barra de ferramentas de navegação com todos os seus botões e controles.

        Responsabilidades:
        - Fornecer botões básicos de navegação (Voltar, Avançar, Recarregar).
        - Exibir a barra de URL com indicador de segurança.
        - Permitir abrir novas abas.
        - Incluir controles de privacidade (JavaScript e bloqueador de conteúdo).
        - Incluir botões auxiliares (Trocar Proxy, Favoritos, Editor e PDF).
        """

        # Criação da barra de navegação
        self.nav_toolbar = QToolBar("Navegação")
        self.nav_toolbar.setMovable(True)  # Permite reposicionar a barra
        self.addToolBar(self.nav_toolbar)

        # --- Botões de navegação padrão ---
        self.btn_voltar = QToolButton()
        self.btn_voltar.setIcon(self.style().standardIcon(QStyle.SP_ArrowBack))
        self.btn_voltar.setToolTip("Voltar (Alt + Seta Esquerda)")

        self.btn_avancar = QToolButton()
        self.btn_avancar.setIcon(self.style().standardIcon(QStyle.SP_ArrowForward))
        self.btn_avancar.setToolTip("Avançar (Alt + Seta Direita)")

        self.btn_recarregar = QToolButton()
        self.btn_recarregar.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.btn_recarregar.setToolTip("Recarregar (F5)")

        # Conexão dos botões às ações de navegação
        self.btn_voltar.clicked.connect(lambda: self._executar_se_webview(lambda aba: aba.back()))
        self.btn_avancar.clicked.connect(lambda: self._executar_se_webview(lambda aba: aba.forward()))
        self.btn_recarregar.clicked.connect(lambda: self._executar_se_webview(lambda aba: aba.reload()))

        # Adiciona os botões à barra
        self.nav_toolbar.addWidget(self.btn_voltar)
        self.nav_toolbar.addWidget(self.btn_avancar)
        self.nav_toolbar.addWidget(self.btn_recarregar)

        # --- Campo de URL com indicador de segurança ---
        url_container = QWidget()
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(5, 0, 5, 0)

        # Indicador de segurança (ex.: HTTPS, certificados, etc.)
        self.security_indicator_label = QLabel("ⓘ")
        self.security_indicator_label.setToolTip("Informações do site")
        url_layout.addWidget(self.security_indicator_label)

        # Barra de URL
        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navegar_para_url)  # Pressionar Enter navega
        url_layout.addWidget(self.url_bar)

        self.nav_toolbar.addWidget(url_container)

        # --- Botão para abrir nova aba ---
        btn_nova_aba = QPushButton("+")
        btn_nova_aba.setFixedSize(30, 30)
        btn_nova_aba.setToolTip("Nova Aba (Ctrl+T)")
        btn_nova_aba.clicked.connect(lambda: self.adicionar_nova_aba())
        self.nav_toolbar.addWidget(btn_nova_aba)

        # --- Botão para habilitar/desabilitar JavaScript ---
        self.btn_js = QPushButton("JS")
        self.btn_js.setCheckable(True)
        self.btn_js.toggled.connect(self.toggle_javascript)
        self.nav_toolbar.addWidget(self.btn_js)

        # --- Botão para ativar/desativar bloqueador de conteúdo ---
        self.btn_blocker = QPushButton("Block")
        self.btn_blocker.setCheckable(True)
        self.btn_blocker.toggled.connect(self.toggle_blocker)
        self.nav_toolbar.addWidget(self.btn_blocker)

        # --- Botão para alternar User-Agent ---
        self._criar_botao_user_agent()

        # --- Botão para trocar proxy ---
        btn_switch_proxy = QPushButton("Trocar Proxy")
        btn_switch_proxy.clicked.connect(self.trocar_proxy)
        self.nav_toolbar.addWidget(btn_switch_proxy)

        # --- Botão para salvar/remover favoritos ---
        self.btn_toggle_favorito = QPushButton("★ Salvar")
        self.btn_toggle_favorito.clicked.connect(self.toggle_favorito)
        self.nav_toolbar.addWidget(self.btn_toggle_favorito)

        # --- Botão para abrir editor HTML ---
        btn_editor = QPushButton("Editor")
        btn_editor.clicked.connect(lambda: self.abrir_editor_html())
        self.nav_toolbar.addWidget(btn_editor)

        # --- Botão para abrir PDFs ---
        btn_pdf = QPushButton("Abrir PDF")
        btn_pdf.clicked.connect(self.abrir_pdf_dialogo)
        self.nav_toolbar.addWidget(btn_pdf)
    
    def _criar_botao_user_agent(self):
        """
        Cria o botão de menu para seleção do User-Agent.

        Responsabilidades:
        - Exibir o User-Agent atualmente selecionado no botão.
        - Fornecer um menu suspenso (popup) com opções de User-Agent.
        - Permitir alternar entre o User-Agent padrão e os personalizados definidos.
        - Garantir que apenas uma opção de User-Agent esteja ativa por vez.
        """
        # Botão principal que exibe o User-Agent atual
        self.ua_button = QToolButton()
        self.ua_button.setText(self.current_ua_name)
        self.ua_button.setPopupMode(QToolButton.InstantPopup)  # Abre o menu imediatamente ao clicar

        # Criação do menu e grupo de ações (exclusivas)
        ua_menu = QMenu(self)
        ua_group = QActionGroup(self)
        ua_group.setExclusive(True)  # Apenas uma opção pode estar ativa

        # --- Opção de User-Agent padrão ---
        default_ua_action = QAction("UA Padrão", self, checkable=True)
        default_ua_action.setChecked(True)  # Selecionado por padrão
        default_ua_action.triggered.connect(
            lambda: self.definir_user_agent_global("UA Padrão", "")
        )
        ua_group.addAction(default_ua_action)
        ua_menu.addAction(default_ua_action)

        # --- Opções de User-Agents personalizados ---
        for name, ua_string in self.user_agents.items():
            action = QAction(name, self, checkable=True)
            # Usa lambda com parâmetros nomeados para evitar captura tardia
            action.triggered.connect(
                lambda checked, n=name, ua=ua_string: self.definir_user_agent_global(n, ua)
            )
            ua_group.addAction(action)
            ua_menu.addAction(action)

        # Associa o menu ao botão e adiciona à barra de navegação
        self.ua_button.setMenu(ua_menu)
        self.nav_toolbar.addWidget(self.ua_button)


    def _criar_barra_favoritos(self):
        """
        Cria a barra de ferramentas dedicada aos favoritos (bookmarks).

        Responsabilidades:
        - Inserir uma nova barra de ferramentas abaixo da barra de navegação.
        - Permitir que os favoritos sejam exibidos como botões clicáveis.
        - Tornar a barra móvel, permitindo que o usuário a reposicione.
        """
        # Insere uma quebra para que a barra de favoritos fique abaixo da de navegação
        self.addToolBarBreak()

        # Cria a barra de favoritos
        self.bookmarks_toolbar = QToolBar("Favoritos")
        self.bookmarks_toolbar.setMovable(True)  # Usuário pode reposicionar
        self.addToolBar(self.bookmarks_toolbar)

    def _criar_barra_busca(self):
        """
        Cria a barra de ferramentas de busca na página, inicialmente oculta.

        Responsabilidades:
        - Fornecer um campo de entrada para o usuário digitar o termo de busca.
        - Permitir navegar entre as ocorrências (anterior e próxima).
        - Permitir fechar a barra de busca e limpar os destaques.
        - Ser exibida na parte inferior da janela quando ativada.
        """
        # Criação da barra de busca
        self.find_toolbar = QToolBar("Busca")

        # Campo de entrada para o termo de busca
        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Buscar na página...")
        self.find_input.textChanged.connect(self.buscar_texto)
        self.find_toolbar.addWidget(self.find_input)

        # Botão para buscar ocorrência anterior
        btn_prev = QPushButton("<")
        btn_prev.clicked.connect(self.buscar_anterior)
        self.find_toolbar.addWidget(btn_prev)

        # Botão para buscar próxima ocorrência
        btn_next = QPushButton(">")
        btn_next.clicked.connect(self.buscar_proximo)
        self.find_toolbar.addWidget(btn_next)

        # Botão para fechar a barra de busca
        btn_close_find = QPushButton("X")
        btn_close_find.clicked.connect(self.fechar_busca)
        self.find_toolbar.addWidget(btn_close_find)

        # Adiciona a barra na parte inferior da janela
        self.addToolBar(Qt.ToolBarArea.BottomToolBarArea, self.find_toolbar)

        # Inicialmente oculta até ser chamada
        self.find_toolbar.hide()


    def _criar_paineis(self):
        """
        Cria os painéis (dock widgets) de Rede e IA.

        Responsabilidades:
        - Painel de Rede:
            - Exibe informações sobre requisições de rede.
            - Permite interceptar e inspecionar requisições (via TamperDialog).
            - É adicionado na parte inferior da janela e começa oculto.
        - Painel de IA:
            - Exibe o assistente de IA integrado (AIPanel).
            - Permite enviar prompts e receber respostas.
            - É adicionado na lateral direita da janela e começa oculto.
        """
        # --- Painel de Rede ---
        self.network_dock = QDockWidget("Painel de Rede", self)
        self.network_panel = NetworkPanel()
        self.network_dock.setWidget(self.network_panel)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.network_dock)
        self.network_dock.hide()

        # Conecta o sinal do painel de rede para abrir o diálogo de interceptação
        self.network_panel.request_tamper_requested.connect(self.abrir_dialogo_tamper)

        # --- Painel de IA ---
        self.ai_dock = QDockWidget("Assistente IA", self)
        self.ai_panel = AIPanel()
        self.ai_dock.setWidget(self.ai_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ai_dock)
        self.ai_dock.hide()

        # Conecta o envio de prompt do painel de IA ao processamento
        self.ai_panel.prompt_enviado.connect(self.processar_prompt_ia)

    def _carregar_dados_iniciais(self):
        """Carrega todas as configurações e dados salvos de arquivos."""
        self.carregar_config()
        self.carregar_historico()
        self.carregar_proxies()
        self.carregar_favoritos()
        self.atualizar_barra_favoritos()
        self.carregar_blocklist()
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.handle_download_request)

    # --------------------------------------------------------------------------
    # --- MÉTODOS PRINCIPAIS E FUNCIONALIDADES ---
    # --------------------------------------------------------------------------

    def _executar_se_webview(self, acao_lambda):
        """
        Executa uma ação na aba atual somente se ela for um WebView.

        Responsabilidades:
        - Verificar se a aba atual é uma instância de WebView.
        - Caso seja, executar a ação passada como parâmetro (função lambda).
        - Evita erros ao tentar aplicar ações de navegação em abas que não sejam páginas web
          (por exemplo, editores de texto ou painéis internos).
        
        :param acao_lambda: Função (lambda) que recebe a aba como argumento e executa a ação desejada.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            acao_lambda(aba)


    def carregar_config(self):
        """
        Carrega a configuração do navegador a partir de um arquivo JSON.

        Responsabilidades:
        - Ler o arquivo de configuração definido em `self.config_file`.
        - Extrair a chave de API (api_key) usada pelo assistente de IA.
        - Caso o arquivo não exista ou esteja corrompido, inicializa a chave como vazia.

        Observação:
        - O uso de `try/except` garante robustez contra erros de leitura ou parsing.
        """
        try:
            with open(self.config_file, "r", encoding='utf-8') as f:
                config = json.load(f)
                self.api_key = config.get("api_key", "")
        except (FileNotFoundError, json.JSONDecodeError):
            self.api_key = ""


    def salvar_config(self):
        """
        Salva a configuração atual do navegador em um arquivo JSON.

        Responsabilidades:
        - Persistir a chave de API (api_key) para uso futuro.
        - Garantir que o arquivo seja gravado em UTF-8 e formatado com indentação
          para facilitar leitura manual.

        Observação:
        - Esse método é chamado, por exemplo, quando o usuário insere uma nova chave de API.
        """
        config = {"api_key": self.api_key}
        with open(self.config_file, "w", encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
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


    def definir_user_agent_global(self, name, user_agent_string):
        """
        Define o User-Agent global do navegador.

        Responsabilidades:
        - Atualizar o User-Agent padrão do perfil global (`QWebEngineProfile.defaultProfile`).
        - Se nenhum User-Agent for fornecido, utiliza o padrão definido em `self.default_user_agent`.
        - Atualizar o texto do botão de seleção de User-Agent para refletir a escolha atual.
        - Recarregar a aba atual (se for um WebView) para aplicar o novo User-Agent.

        :param name: Nome amigável do User-Agent (ex.: "Chrome", "Firefox", "UA Padrão").
        :param user_agent_string: String completa do User-Agent a ser usada.
        """
        final_ua = user_agent_string or self.default_user_agent
        QWebEngineProfile.defaultProfile().setHttpUserAgent(final_ua)

        # Atualiza o estado interno e a interface
        self.current_ua_name = name
        self.ua_button.setText(self.current_ua_name)

        # Recarrega a aba atual para aplicar o novo User-Agent
        self._executar_se_webview(lambda aba: aba.reload())


    def on_link_hovered(self, url):
        """
        Atualiza a barra de status quando o usuário passa o mouse sobre um link.

        Responsabilidades:
        - Exibir a URL do link na barra de status enquanto o mouse estiver sobre ele.
        - Se não houver link (mouse fora de links), exibir a mensagem de status do proxy.

        :param url: URL do link atualmente sob o cursor do mouse.
        """
        self.status_bar.showMessage(url if url else self.proxy_status_message)


    def toggle_full_screen(self, checked):
        """
        Alterna entre o modo de tela cheia e o modo normal da janela.

        Responsabilidades:
        - Se `checked` for True, coloca a janela em tela cheia.
        - Se `checked` for False, restaura para o modo normal.

        :param checked: Booleano indicando o estado desejado (True = tela cheia).
        """
        self.showFullScreen() if checked else self.showNormal()

    def keyPressEvent(self, event):
        """
        Sobrescreve o evento de tecla pressionada para tratar atalhos especiais.

        Responsabilidades:
        - Se a tecla pressionada for ESC e a janela estiver em tela cheia:
            - Desmarca a ação de tela cheia (`fullscreen_action`), retornando ao modo normal.
        - Caso contrário, delega o tratamento ao comportamento padrão da superclasse.
        """
        if event.key() == Qt.Key_Escape and self.isFullScreen():
            if hasattr(self, 'fullscreen_action'):
                self.fullscreen_action.setChecked(False)
        else:
            super().keyPressEvent(event)


    def toggle_full_screen_shortcut(self):
        """
        Alterna o estado de tela cheia através de um atalho de teclado ou ação.

        Responsabilidades:
        - Inverte o estado da ação `fullscreen_action` (checked/unchecked).
        - Isso aciona automaticamente a lógica de entrar ou sair do modo tela cheia.
        """
        if hasattr(self, 'fullscreen_action'):
            self.fullscreen_action.setChecked(not self.fullscreen_action.isChecked())


    def toggle_menu_bar_visibility(self):
        """
        Alterna a visibilidade da barra de menus.

        Responsabilidades:
        - Se a barra de menus estiver visível, oculta.
        - Se estiver oculta, torna visível novamente.
        - Útil para maximizar o espaço de navegação.
        """
        menu_bar = self.menuBar()
        menu_bar.setVisible(not menu_bar.isVisible())


    def zoom_in(self):
        """
        Aumenta o nível de zoom da aba atual.

        - Incrementa o fator de zoom em +0.1.
        - Executa apenas se a aba atual for um WebView.
        """
        self._executar_se_webview(lambda aba: aba.setZoomFactor(aba.zoomFactor() + 0.1))


    def zoom_out(self):
        """
        Diminui o nível de zoom da aba atual.

        - Reduz o fator de zoom em -0.1.
        - Executa apenas se a aba atual for um WebView.
        """
        self._executar_se_webview(lambda aba: aba.setZoomFactor(aba.zoomFactor() - 0.1))


    def zoom_reset(self):
        """
        Restaura o nível de zoom da aba atual para o padrão (100%).

        - Define o fator de zoom como 1.0.
        - Executa apenas se a aba atual for um WebView.
        """
        self._executar_se_webview(lambda aba: aba.setZoomFactor(1.0))


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


    def abrir_pdf_dialogo(self):
        """
        Abre um diálogo para seleção de arquivo PDF e o exibe em uma nova aba.

        Responsabilidades:
        - Exibir um diálogo de seleção de arquivo filtrado para PDFs.
        - Se o usuário selecionar um arquivo válido:
            - Cria uma nova aba com o visualizador de PDF.
            - Carrega o arquivo selecionado diretamente no WebView.
        """
        caminho, _ = QFileDialog.getOpenFileName(self, "Abrir PDF", "", "Arquivos PDF (*.pdf)")
        if caminho:
            self.adicionar_nova_aba(QUrl.fromLocalFile(caminho), "Visualizador PDF")

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


    def preview_html(self):
        """
        Renderiza a pré-visualização do HTML no editor lado a lado (SplitEditor).

        - Obtém a aba atual.
        - Se for um SplitEditor, chama `render_preview()` para atualizar a visualização.
        """
        aba_atual = self.aba_atual()
        if isinstance(aba_atual, SplitEditor):
            aba_atual.render_preview()

    def setup_shortcuts(self):
        """
        Configura todos os atalhos de teclado do navegador.

        Responsabilidades:
        - Criar instâncias de QShortcut associadas à janela principal.
        - Mapear combinações de teclas para ações específicas do navegador.
        - Garantir que o usuário tenha acesso rápido a funcionalidades comuns.

        Atalhos configurados:
        - Ctrl+U → Exibir código-fonte da aba atual.
        - Ctrl+F → Abrir a barra de busca na página.
        - Ctrl+Shift+A → Abrir o painel de Inteligência Artificial.
        - Ctrl+Shift+I → Alternar o painel de rede (DevTools).
        - Ctrl+T → Abrir uma nova aba.
        - Ctrl+N → Abrir o editor de HTML.
        - F5 → Recarregar a aba atual.
        - Ctrl+H → Abrir o histórico de navegação.
        - F11 → Alternar modo tela cheia.
        - Ctrl+M → Alternar visibilidade da barra de menus.
        - Ctrl+Shift+L → Alternar visibilidade da barra de navegação.
        - Ctrl+Shift+B → Alternar visibilidade da barra de favoritos.
        - Ctrl+= → Aumentar zoom da aba atual.
        - Ctrl+- → Diminuir zoom da aba atual.
        - Ctrl+0 → Resetar zoom para 100%.
        - Ctrl+Tab → Selecionar próxima aba.
        - Ctrl+Shift+Tab → Selecionar aba anterior.
        - Backspace (StandardKey.Back) → Voltar na navegação da aba atual.
        - Shift+Backspace ou equivalente (StandardKey.Forward) → Avançar na navegação da aba atual.
        """
        QShortcut(QKeySequence("Ctrl+U"), self).activated.connect(self.ver_codigo_fonte_aba_atual)
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self.abrir_busca)
        QShortcut(QKeySequence("Ctrl+Shift+A"), self).activated.connect(self.abrir_painel_ia)
        QShortcut(QKeySequence("Ctrl+Shift+I"), self).activated.connect(self.toggle_network_panel)
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.adicionar_nova_aba)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.abrir_editor_html)
        QShortcut(QKeySequence("F5"), self).activated.connect(
            lambda: self._executar_se_webview(lambda aba: aba.reload())
        )
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.abrir_aba_historico)
        QShortcut(QKeySequence("F11"), self).activated.connect(self.toggle_full_screen_shortcut)
        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self.toggle_menu_bar_visibility)
        QShortcut(QKeySequence("Ctrl+Shift+L"), self).activated.connect(self.toggle_nav_bar_visibility)
        QShortcut(QKeySequence("Ctrl+Shift+B"), self).activated.connect(self.toggle_bookmarks_bar_visibility)
        QShortcut(QKeySequence("Ctrl+="), self).activated.connect(self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self).activated.connect(self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self).activated.connect(self.zoom_reset)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self.select_next_tab)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self.select_previous_tab)
        QShortcut(QKeySequence.StandardKey.Back, self).activated.connect(
            lambda: self._executar_se_webview(lambda aba: aba.back())
        )
        QShortcut(QKeySequence.StandardKey.Forward, self).activated.connect(
            lambda: self._executar_se_webview(lambda aba: aba.forward())
        )
        
    def toggle_nav_bar_visibility(self):
        """
        Alterna a visibilidade da barra de navegação.

        Responsabilidades:
        - Verifica se existe a ação `toggle_nav_bar_action`.
        - Inverte o estado de "checked" dessa ação, o que automaticamente
          mostra ou oculta a barra de navegação.
        """
        if hasattr(self, 'toggle_nav_bar_action'):
            self.toggle_nav_bar_action.setChecked(not self.toggle_nav_bar_action.isChecked())


    def toggle_bookmarks_bar_visibility(self):
        """
        Alterna a visibilidade da barra de favoritos.

        Responsabilidades:
        - Verifica se existe a ação `toggle_bookmarks_bar_action`.
        - Inverte o estado de "checked" dessa ação, o que automaticamente
          mostra ou oculta a barra de favoritos.
        """
        if hasattr(self, 'toggle_bookmarks_bar_action'):
            self.toggle_bookmarks_bar_action.setChecked(not self.toggle_bookmarks_bar_action.isChecked())


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


    def ver_codigo_fonte_aba_atual(self):
        """
        Exibe o código-fonte da aba atual.

        - Executa a ação `ver_codigo_fonte()` apenas se a aba atual for um WebView.
        - Utiliza `_executar_se_webview` para garantir segurança.
        """
        self._executar_se_webview(lambda aba: aba.ver_codigo_fonte())


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
        icon = self.create_svg_icon(get_data_path(path), QColor(color))
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


if __name__ == "__main__":
    """
    Ponto de entrada principal da aplicação.

    Responsabilidades:
    - Criar a instância da aplicação Qt (`QApplication`).
    - Carregar traduções (se a função `carregar_traducoes` estiver disponível).
    - Definir a localidade padrão como português do Brasil (`pt_BR`).
    - Criar e exibir a janela principal do navegador (`Navegador`).
    - Executar o loop de eventos da aplicação até o encerramento.
    """

    # Cria a aplicação Qt
    app = QApplication(sys.argv)

    # Tenta carregar traduções, se a função estiver definida
    try:
        carregar_traducoes(app)
    except NameError:
        pass  # Ignora se a função não existir

    # Define a localidade padrão como português do Brasil
    QLocale.setDefault(QLocale("pt_BR"))

    # Cria a janela principal do navegador
    window = Navegador()
    window.showMaximized()  # Exibe a janela em modo maximizado

    # Inicia o loop de eventos da aplicação
    sys.exit(app.exec())