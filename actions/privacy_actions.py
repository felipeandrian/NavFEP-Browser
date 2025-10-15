# actions/privacy_actions.py

"""
Este módulo contém o mixin PrivacyActions, que encapsula as funcionalidades
relacionadas com a privacidade e o controlo de conteúdo do navegador.

As suas responsabilidades incluem:
- Carregar a lista de domínios a serem bloqueados (blocklist).
- Implementar a lógica para ativar/desativar o bloqueador de conteúdo por aba.
- Implementar a lógica para ativar/desativar a execução de JavaScript por aba.
- Sincronizar o estado visual dos botões de controlo na interface do utilizador.
"""

# --- Imports da Biblioteca Padrão ---
import json

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtWebEngineCore import QWebEngineSettings

# --- Imports Locais da Aplicação ---
# A classe depende do WebView para obter informações da página atual.
from components import WebView


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