# actions/devtools_actions.py

"""
Este módulo contém o mixin DevToolsActions, que agrupa as ações
relacionadas com as ferramentas de desenvolvedor do navegador.

As suas responsabilidades incluem:
- Controlar a visibilidade do painel de rede.
- Orquestrar a abertura do diálogo de manipulação de requisições (tamper).
"""
# --- Imports Locais da Aplicação ---
# O TamperDialog é a janela de UI para a manipulação de requisições.
from dialogs import TamperDialog

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