# browser_core/ui_builder.py

"""
Este módulo contém o UIBuilderMixin, responsável por construir e configurar
todos os principais elementos da interface de utilizador (UI) da janela do navegador.

Isto inclui a criação de barras de ferramentas, painéis, menus de contexto,
e a configuração de atalhos de teclado globais.
"""

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut, QAction, QActionGroup
from PySide6.QtWidgets import (QToolBar, QTabWidget, QProgressBar, QDockWidget, QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton, QToolButton, QStyle, QMenu)

# --- Imports Locais da Aplicação ---
from panels import AIPanel
# O NetworkPanel foi movido para o pacote 'components.network'
from components.network import NetworkPanel


class UIBuilderMixin:
    """
    Mixin que encapsula toda a lógica de construção da interface do navegador.
    """
	
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
		
	 # --- Slots para os atalhos de visibilidade ---
    
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
            
    # --- Métodos de Controlo de Zoom ---
    
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