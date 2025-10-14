# Arquivo: panels.py

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QLineEdit, QPushButton

class AIPanel(QWidget):
    """
    Painel de interface gráfica para interação com a IA.

    Responsabilidades:
    - Exibir respostas da IA em uma área de saída (QTextBrowser).
    - Permitir que o usuário insira perguntas em um campo de texto.
    - Emitir um sinal quando o usuário enviar um prompt (via botão ou tecla Enter).
    """

    # Sinal emitido quando o usuário envia um prompt de IA
    prompt_enviado = Signal(str)

    def __init__(self, parent=None):
        """
        Inicializa o painel de IA.

        - Cria e organiza os elementos da interface:
            - Área de saída (resposta da IA).
            - Campo de entrada (pergunta do usuário).
            - Botão de envio.
        - Conecta eventos de interação (Enter e clique no botão).
        """
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        # Área de saída para exibir respostas da IA
        self.output_view = QTextBrowser()
        self.output_view.setReadOnly(True)
        self.output_view.setPlaceholderText("A resposta do NavFEP AI aparecerá aqui...")

        # Campo de entrada para o usuário digitar perguntas
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Pergunte algo ao NavFep AI...")
        # Permite enviar a pergunta pressionando Enter
        self.input_field.returnPressed.connect(self._enviar_prompt)

        # Botão de envio
        self.send_button = QPushButton("Enviar")
        self.send_button.clicked.connect(self._enviar_prompt)

        # Adiciona os widgets ao layout vertical
        self.layout().addWidget(self.output_view)
        self.layout().addWidget(self.input_field)
        self.layout().addWidget(self.send_button)

    def _enviar_prompt(self):
        """
        Captura o texto digitado pelo usuário e emite o sinal de envio.

        - Obtém o texto do campo de entrada.
        - Se não estiver vazio:
            - Exibe "Pensando..." na área de saída.
            - Emite o sinal `prompt_enviado` com o texto.
            - Limpa o campo de entrada para a próxima pergunta.
        """
        prompt_text = self.input_field.text().strip()
        if prompt_text:
            self.output_view.setPlainText("Pensando...")
            self.prompt_enviado.emit(prompt_text)
            self.input_field.clear()

    def set_response(self, text):
        """
        Define o texto de resposta na área de saída.

        - Recebe a resposta processada pela IA.
        - Atualiza o QTextBrowser com o conteúdo.
        """
        self.output_view.setPlainText(text)