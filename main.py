# Arquivo: main.py

import sys
import os
import json
from pathlib import Path

# --- CORREÇÃO DE PLATAFORMA PARA LINUX ---
if sys.platform == "linux":
    os.environ['QT_QPA_PLATFORM'] = 'xcb'
    os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --disable-software-rasterizer"

from PySide6.QtCore import QUrl, QLocale, Qt, QLibraryInfo, QTranslator
from PySide6.QtWidgets import QApplication, QMainWindow, QFileDialog
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineCore import QWebEngineProfile

# Módulos do projeto
from panels import AIPanel
from components import WebView, HtmlEditor, UrlInterceptor, NetworkPanel, SplitEditor
from actions import FileMenuActions, BookmarkActions, FindActions, PrivacyActions, DownloadActions, HistoryActions, DevToolsActions, ProtocolActions, AIActions
from browser_core import UIBuilderMixin, TabManagerMixin, EventHandlersMixin

# --- CONSTANTES GLOBAIS ---
# Nomes de arquivos de configuração e dados
CONFIG_FILE_NAME = "navfep_config.json"
HISTORY_FILE_NAME = "navfep_history.json"
PROXIES_FILE = "proxies.json"
BOOKMARKS_FILE = "bookmarks.json"

# URLs e Títulos Padrão
PAGINA_INICIAL_URL = "https://f3l1p3.neocities.org"
PAGINA_INICIAL_TITULO = "Página Inicial"


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
class Navegador(QMainWindow, FileMenuActions, BookmarkActions, FindActions, PrivacyActions, DownloadActions, HistoryActions, DevToolsActions, ProtocolActions, AIActions, UIBuilderMixin, TabManagerMixin, EventHandlersMixin):
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
    
    # --- FUNÇÕES AUXILIARES ---
    def get_data_path(self, filename):
        """Retorna o caminho completo para um arquivo de dados, funcionando tanto em modo script quanto em executável (PyInstaller)."""
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, filename)


    def _configurar_janela(self):
        """Define as propriedades básicas da janela principal (título, tamanho, ícone)."""
        self.setWindowTitle("Navegador do FEP")
        self.setGeometry(100, 100, 1280, 800)
        icon_path = self.get_data_path("navfep.png")
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

    def _carregar_dados_iniciais(self):
        """Carrega todas as configurações e dados salvos de arquivos."""
        self.carregar_config()
        self.carregar_historico()
        self.carregar_proxies()
        self.carregar_favoritos()
        self.atualizar_barra_favoritos()
        self.carregar_blocklist()
        QWebEngineProfile.defaultProfile().downloadRequested.connect(self.handle_download_request)


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

    def preview_html(self):
        """
        Renderiza a pré-visualização do HTML no editor lado a lado (SplitEditor).

        - Obtém a aba atual.
        - Se for um SplitEditor, chama `render_preview()` para atualizar a visualização.
        """
        aba_atual = self.aba_atual()
        if isinstance(aba_atual, SplitEditor):
            aba_atual.render_preview()

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