# Arquivo: dialogs.py

import requests
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, QPlainTextEdit, QLabel, QApplication, QHBoxLayout

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
        
class TamperDialog(QDialog):
    """
    Um diálogo avançado para inspecionar, modificar e reenviar requisições HTTP.
    
    Esta ferramenta permite a manipulação detalhada de requisições, incluindo método,
    URL, cabeçalhos e corpo, e exibe a requisição enviada e a resposta recebida
    lado a lado para análise.
    """
    def __init__(self, request_info, parent=None):
        """
        Construtor da classe TamperDialog.

        Args:
            request_info (dict): Um dicionário contendo os detalhes da requisição a ser editada.
            parent (QWidget, optional): O widget pai deste diálogo. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Editar e Reenviar Requisição")
        self.setMinimumSize(500, 600)

        # --- Inicialização dos Campos da UI com Dados da Requisição ---
        # Popula os campos de edição com os dados da requisição interceptada.
        # Utiliza o método .get() para fornecer valores padrão caso as chaves não existam.
        self.method_input = QLineEdit(request_info.get("method", "GET"))
        self.url_input = QLineEdit(request_info.get("url", ""))

        # Define um conjunto de cabeçalhos padrão para melhorar a usabilidade
        # ao criar uma requisição do zero.
        headers_dict = request_info.get("headers", {})
        chrome_like_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive",
        }

        # Se nenhuma informação de cabeçalho for fornecida, utiliza o conjunto padrão.
        if not headers_dict:
            headers_dict = chrome_like_headers

        # Converte o dicionário de cabeçalhos para um formato de texto multi-linha para edição.
        headers_text = "\n".join([f"{k}: {v}" for k, v in headers_dict.items()])
        self.headers_input = QPlainTextEdit(headers_text)
        
        # Campo de edição para o corpo (body) da requisição.
        self.body_input = QPlainTextEdit()
        self.body_input.setPlaceholderText("Digite ou edite o conteúdo (body) da requisição...")
        self.body_input.setPlainText(request_info.get("body", ""))

        # --- Estrutura do Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("Método:", self.method_input)
        form_layout.addRow("URL:", self.url_input)
        form_layout.addRow("Cabeçalhos (Headers):", self.headers_input)
        form_layout.addRow("Conteúdo (Body):", self.body_input)
        layout.addLayout(form_layout)

        # Botão de ação principal.
        send_button = QPushButton("Enviar Requisição Modificada")
        send_button.clicked.connect(self._send_request)
        layout.addWidget(send_button)
        
        # Layout horizontal para a comparação lado a lado da requisição e resposta.
        comparison_layout = QHBoxLayout()
        
        # Painel esquerdo para exibir os detalhes da requisição enviada.
        sent_layout = QVBoxLayout()
        sent_layout.addWidget(QLabel("Requisição Enviada:"))
        self.sent_output = QPlainTextEdit()
        self.sent_output.setReadOnly(True)
        sent_layout.addWidget(self.sent_output)

        # Painel direito para exibir os detalhes da resposta recebida.
        received_layout = QVBoxLayout()
        received_layout.addWidget(QLabel("Resposta Recebida:"))
        self.received_output = QPlainTextEdit()
        self.received_output.setReadOnly(True)
        received_layout.addWidget(self.received_output)

        comparison_layout.addLayout(sent_layout)
        comparison_layout.addLayout(received_layout)
        layout.addLayout(comparison_layout)

    def _send_request(self):
        """
        Coleta os dados da UI, executa a requisição HTTP e exibe os resultados.
        """
        # Extrai e formata os dados dos campos de edição.
        method = self.method_input.text().upper()
        url = self.url_input.text()
        headers_text = self.headers_input.toPlainText()
        body_text = self.body_input.toPlainText()

        # Converte o texto dos cabeçalhos de volta para um formato de dicionário.
        headers = {}
        for line in headers_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

        # Atualiza a UI para fornecer feedback de que a requisição está em andamento.
        # NOTA: `QApplication.processEvents()` força a atualização, mas a chamada de rede
        # `requests.request()` a seguir é síncrona (bloqueante), o que pode congelar
        # a UI em caso de requisições lentas.
        self.sent_output.setPlainText("Enviando requisição...")
        self.received_output.clear()
        QApplication.processEvents()
        
        try:
            # Executa a requisição HTTP utilizando a biblioteca 'requests'.
            response = requests.request(
                method,
                url,
                headers=headers,
                data=body_text if body_text else None,
                timeout=15  # Define um timeout de 15 segundos para evitar esperas indefinidas.
            )

            # --- Processamento e Exibição dos Resultados ---
            # Formata e exibe os detalhes da requisição que foi efetivamente enviada.
            sent_text = f"{method} {url}\n\n"
            sent_text += "\n".join([f"{k}: {v}" for k, v in response.request.headers.items()])
            if body_text:
                sent_text += f"\n\n--- BODY ENVIADO ---\n{body_text}"
            self.sent_output.setPlainText(sent_text)

            # Formata e exibe os detalhes da resposta recebida do servidor.
            recv_text = f"STATUS: {response.status_code}\n\n"
            recv_text += "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
            recv_text += "\n\n--- BODY RECEBIDO ---\n"
            # Trunca o corpo da resposta para evitar problemas de performance com conteúdos muito grandes.
            recv_text += response.text[:2000]
            self.received_output.setPlainText(recv_text)

        except Exception as e:
            # Captura exceções de rede (ex: timeout, erro de DNS) e exibe a mensagem de erro na UI.
            self.sent_output.setPlainText("Erro ao enviar requisição")
            self.received_output.setPlainText(str(e))