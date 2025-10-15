# dialogs/tamper_dialog.py

import requests
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QDialog, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, QPlainTextEdit, QLabel, QHBoxLayout

# WORKER PARA TAREFAS DE REDE
class RequestWorker(QObject):
    """
    Worker que executa uma requisição 'requests' em uma QThread separada para não congelar a UI.
    
    Esta classe é projetada para ser movida para uma thread secundária. Ela realiza a
    operação de rede bloqueante e comunica o resultado de volta para a thread principal
    de forma segura através de sinais do Qt.
    """
    # Sinal emitido com o objeto de resposta completo em caso de sucesso.
    response_ready = Signal(object)
    # Sinal emitido com a mensagem de erro em caso de falha.
    request_failed = Signal(str)
    # Sinal emitido sempre que a tarefa é concluída, seja com sucesso ou falha.
    finished = Signal()

    def __init__(self, method, url, headers, body):
        """
        Construtor do RequestWorker.
        
        Args:
            method (str): O método HTTP (ex: 'GET', 'POST').
            url (str): A URL do endpoint.
            headers (dict): Dicionário de cabeçalhos da requisição.
            body (str): O corpo (payload) da requisição.
        """
        super().__init__()
        self.method, self.url, self.headers, self.body = method, url, headers, body

    def run(self):
        """
        O método principal que é executado na thread secundária.
        Realiza a chamada de rede bloqueante e emite os sinais apropriados.
        """
        try:
            response = requests.request(
                self.method, self.url, headers=self.headers,
                data=self.body.encode('utf-8') if self.body else None,
                timeout=15
            )
            # Emite o resultado para o slot conectado na thread principal.
            self.response_ready.emit(response)
        except Exception as e:
            # Emite o erro para o slot de tratamento de erros na thread principal.
            self.request_failed.emit(str(e))
        finally:
            # Garante que o sinal 'finished' seja sempre emitido para a limpeza da thread.
            self.finished.emit()


class TamperDialog(QDialog):
    """
    Um diálogo avançado para inspecionar, modificar e reenviar requisições HTTP
    de forma assíncrona, prevenindo o congelamento da interface.
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
        self.setMinimumSize(600, 700) # Aumentado para melhor visualização

        # --- Inicialização dos Campos da UI com Dados da Requisição ---
        self.method_input = QLineEdit(request_info.get("method", "GET"))
        self.url_input = QLineEdit(request_info.get("url", ""))

        headers_dict = request_info.get("headers", {})
        chrome_like_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        }
        if not headers_dict: headers_dict = chrome_like_headers
        headers_text = "\n".join([f"{k}: {v}" for k, v in headers_dict.items()])
        self.headers_input = QPlainTextEdit(headers_text)
        
        self.body_input = QPlainTextEdit(request_info.get("body", "")); self.body_input.setPlaceholderText("Corpo (body) da requisição...")

        # --- Estrutura do Layout ---
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        form_layout.addRow("Método:", self.method_input); form_layout.addRow("URL:", self.url_input)
        form_layout.addRow("Cabeçalhos (Headers):", self.headers_input); form_layout.addRow("Conteúdo (Body):", self.body_input)
        layout.addLayout(form_layout)

        self.send_button = QPushButton("Enviar Requisição Modificada")
        self.send_button.clicked.connect(self._send_request)
        layout.addWidget(self.send_button)
        
        comparison_layout = QHBoxLayout()
        sent_layout = QVBoxLayout(); sent_layout.addWidget(QLabel("Requisição Enviada:")); self.sent_output = QPlainTextEdit(); self.sent_output.setReadOnly(True); sent_layout.addWidget(self.sent_output)
        received_layout = QVBoxLayout(); received_layout.addWidget(QLabel("Resposta Recebida:")); self.received_output = QPlainTextEdit(); self.received_output.setReadOnly(True); received_layout.addWidget(self.received_output)
        comparison_layout.addLayout(sent_layout); comparison_layout.addLayout(received_layout)
        layout.addLayout(comparison_layout)

    def _send_request(self):
        """
        Slot que INICIA a requisição. Em vez de executar a chamada de rede diretamente,
        ele cria e inicia o worker e a thread para uma operação assíncrona.
        """
        self.send_button.setEnabled(False)
        self.sent_output.setPlainText("A enviar requisição...")
        self.received_output.clear()

        method = self.method_input.text().upper()
        url = self.url_input.text()
        headers_text = self.headers_input.toPlainText()
        body = self.body_input.toPlainText()
        headers = {k.strip(): v.strip() for line in headers_text.split("\n") if ":" in line for k, v in [line.split(":", 1)]}

        # --- Lógica de Thread Assíncrona ---
        self.thread = QThread()
        self.worker = RequestWorker(method, url, headers, body)
        self.worker.moveToThread(self.thread)

        self.thread.started.connect(self.worker.run)
        self.worker.response_ready.connect(self._on_response_ready)
        self.worker.request_failed.connect(self._on_request_failed)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_response_ready(self, response):
        """
        Slot para ATUALIZAR A UI quando a resposta da thread chegar com sucesso.
        """
        sent_text = f"{response.request.method} {response.request.url}\n\n"
        sent_text += "\n".join([f"{k}: {v}" for k, v in response.request.headers.items()])
        if response.request.body:
            sent_text += f"\n\n--- CORPO ENVIADO ---\n{response.request.body.decode('utf-8', 'ignore')}"
        self.sent_output.setPlainText(sent_text)

        recv_text = f"STATUS: {response.status_code}\n\n"
        recv_text += "\n".join([f"{k}: {v}" for k, v in response.headers.items()])
        recv_text += f"\n\n--- CORPO RECEBIDO ---\n{response.text[:4000]}"
        self.received_output.setPlainText(recv_text)

        self.send_button.setEnabled(True)

    def _on_request_failed(self, error_message):
        """
        Slot para ATUALIZAR A UI em caso de erro na requisição.
        """
        self.sent_output.setPlainText("Erro ao enviar requisição")
        self.received_output.setPlainText(error_message)
        self.send_button.setEnabled(True)