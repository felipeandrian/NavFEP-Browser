# actions/download_actions.py

"""
Este módulo contém o mixin DownloadActions, responsável por gerir o ciclo de
vida dos downloads de ficheiros iniciados pelo QWebEngine.

As suas responsabilidades incluem:
- Intercetar o sinal de 'downloadRequested'.
- Apresentar um diálogo 'Salvar Ficheiro' ao utilizador.
- Monitorizar o progresso do download e atualizar a barra de status.
- Lidar com os estados finais do download (concluído, cancelado, interrompido).
"""

# --- Imports da Biblioteca Padrão ---
import os
from pathlib import Path

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtWidgets import QFileDialog
from PySide6.QtWebEngineCore import QWebEngineDownloadRequest

class DownloadActions:
    """
    Mixin que implementa as ações relacionadas a downloads de arquivos no navegador.

    Responsabilidades:
    - Interceptar solicitações de download.
    - Permitir ao usuário escolher o local de salvamento.
    - Monitorar o progresso do download.
    - Exibir mensagens de status e notificar conclusão, cancelamento ou falha.
    """

    def handle_download_request(self, download: QWebEngineDownloadRequest):
        """
        Manipula uma nova solicitação de download.

        - Sugere o diretório padrão de downloads do usuário.
        - Abre um diálogo para que o usuário escolha onde salvar o arquivo.
        - Caso o usuário confirme:
            - Define o diretório e nome do arquivo no objeto `download`.
            - Conecta sinais para monitorar progresso e estado final.
            - Exibe mensagem de status e inicia o download.
            - Adiciona o download à lista de downloads ativos.
        - Caso o usuário cancele:
            - Cancela o download e exibe mensagem no console.
        """
        suggested_path = os.path.join(str(Path.home()), "Downloads", download.downloadFileName())
        file_path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", suggested_path)

        if file_path:
            download.setDownloadDirectory(os.path.dirname(file_path))
            download.setDownloadFileName(os.path.basename(file_path))

            # Conecta sinais para progresso e término
            download.receivedBytesChanged.connect(lambda: self.update_download_progress(download))
            download.stateChanged.connect(lambda state, download=download: self.finish_download(state, download))

            self.status_bar.showMessage(f"Baixando {os.path.basename(file_path)}...")
            download.accept()
            self.active_downloads.append(download)
        else:
            print("Download cancelado.")
            download.cancel()

    def update_download_progress(self, download: QWebEngineDownloadRequest):
        """
        Atualiza o progresso do download em tempo real.

        - Obtém bytes recebidos e total esperado.
        - Se o total for conhecido, calcula a porcentagem concluída.
        - Caso contrário, exibe apenas o tamanho já baixado em KB.
        - Atualiza a barra de status com a informação.
        """
        bytes_received = download.receivedBytes()
        bytes_total = download.totalBytes()
        if bytes_total > 0:
            percent = int((bytes_received / bytes_total) * 100)
            self.status_bar.showMessage(f"Baixando... {percent}%")
        else:
            self.status_bar.showMessage(f"Baixando... {bytes_received / 1024:.0f} KB")

    def finish_download(self, state, download: QWebEngineDownloadRequest):
        """
        Trata o término de um download, exibindo mensagens adequadas.

        - Se concluído com sucesso: mostra mensagem de "Download concluído".
        - Se cancelado: mostra mensagem de "Download cancelado".
        - Se interrompido/falhou: mostra mensagem de erro.
        - Remove o download da lista de downloads ativos.
        """
        if state == QWebEngineDownloadRequest.DownloadCompleted:
            self.status_bar.showMessage("Download concluído!", 5000)
        elif state == QWebEngineDownloadRequest.DownloadCancelled:
            self.status_bar.showMessage("Download cancelado.", 5000)
        elif state == QWebEngineDownloadRequest.DownloadInterrupted:
            self.status_bar.showMessage("Download interrompido/falhou.", 5000)

        if download in self.active_downloads:
            self.active_downloads.remove(download)