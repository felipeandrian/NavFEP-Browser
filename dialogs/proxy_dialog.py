# dialogs/proxy_dialog.py

from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QFormLayout

class ProxyDialog(QDialog):
    """
    Um diálogo para capturar os detalhes de configuração de um proxy a partir do utilizador.

    Esta classe cria uma interface de utilizador simples com campos para um apelido,
    host e porta. Os widgets são expostos como atributos de instância para permitir
    que a lógica de conexão de sinais seja gerida pela classe que instancia este diálogo.
    """

    def __init__(self, parent=None):
        """
        Construtor da classe ProxyDialog.

        Args:
            parent (QWidget, optional): O widget pai deste diálogo. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Configurar Proxy")

        # --- Definição dos Widgets da UI ---
        # Campo para um alias opcional definido pelo utilizador para o proxy.
        self.apelido_input = QLineEdit()
        self.apelido_input.setPlaceholderText("Ex: Proxy de Casa (opcional)")

        # Campo para o endereço do host do proxy (IP ou domínio).
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("Ex: 177.44.22.11")
        
        # Campo para a porta do proxy com uma máscara de input para restringir a entrada a 5 dígitos.
        self.port_input = QLineEdit()
        self.port_input.setInputMask("00000;")
        self.port_input.setPlaceholderText("Ex: 8080")

        # --- Estrutura do Layout ---
        # Utiliza-se um QFormLayout para uma apresentação limpa e alinhada de rótulos e campos.
        layout = QFormLayout(self)
        layout.addRow("Apelido (Opcional):", self.apelido_input)
        layout.addRow("Host:", self.host_input)
        layout.addRow("Porta:", self.port_input)

        # Define os botões de ação do diálogo.
        self.temp_use_button = QPushButton("Usar Temporariamente")
        self.save_and_use_button = QPushButton("Salvar e Usar")
        self.disable_button = QPushButton("Desativar Proxy")
        self.close_button = QPushButton("Fechar")

        # Agrupa os botões de ação num layout vertical para organização visual.
        button_layout = QVBoxLayout()
        button_layout.addWidget(self.temp_use_button)
        button_layout.addWidget(self.save_and_use_button)
        button_layout.addWidget(self.disable_button)
        button_layout.addWidget(self.close_button)
        layout.addRow(button_layout)

        # Conecta o botão de fechar ao slot 'reject' padrão do QDialog, que fecha a janela
        # e retorna um resultado correspondente (QDialog.Rejected).
        self.close_button.clicked.connect(self.reject)