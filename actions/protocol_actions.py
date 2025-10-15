# actions/protocol_actions.py

"""
Este módulo contém o mixin ProtocolActions, responsável por implementar
suporte a protocolos de rede não-padrão, como o Gopher.

A classe lida com a análise de URLs específicas do protocolo, estabelece
conexões de socket de baixo nível, processa a resposta e a traduz para um
formato HTML renderizável pelo motor web.
"""

# --- Imports da Biblioteca Padrão ---
import socket
import base64

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtCore import QUrl

# --- Imports Locais da Aplicação ---
# A classe depende do WebView como o alvo para renderizar o HTML gerado.
from components import WebView

class ProtocolActions:
    """
    Mixin para lidar com protocolos alternativos, como o Gopher.

    Responsabilidades:
    - Interpretar e processar requisições Gopher.
    - Converter respostas em HTML para exibição no navegador.
    - Suportar diferentes tipos de conteúdo (texto, menus, imagens).
    """

    def handle_gopher_request(self, url, tab):
        """
        Manipula uma requisição Gopher e renderiza o resultado na aba especificada.

        - Analisa a URL para extrair host, porta, seletor e tipo de conteúdo.
        - Estabelece conexão TCP com o servidor Gopher.
        - Envia o seletor e recebe a resposta bruta.
        - Se o tipo for imagem (g, I, p), converte os dados em HTML com <img>.
        - Caso contrário, interpreta o mapa Gopher (menus/texto) e converte em HTML.
        - Em caso de erro, exibe mensagem de falha na aba.
        """
        try:
            # Extrai tipo de conteúdo da query string, se presente
            gopher_type = None
            if "?gopher_type=" in url:
                url_parts = url.split("?gopher_type=")
                url = url_parts[0]
                gopher_type = url_parts[1]

            # Extrai host, porta e seletor da URL
            parts = url.split("//")[1].split("/")
            host_port = parts[0].split(":")
            host = host_port[0]
            port = int(host_port[1]) if len(host_port) > 1 else 70
            selector = "/" + "/".join(parts[1:]) if len(parts) > 1 else ""

            # Conexão TCP com servidor Gopher
            with socket.create_connection((host, port), timeout=10) as s:
                s.sendall((selector + "\r\n").encode('utf-8'))
                response_data = b""
                while True:
                    chunk = s.recv(8192)
                    if not chunk:
                        break
                    response_data += chunk

            # Decide como processar a resposta
            if gopher_type in ('g', 'I', 'p'):
                # Conteúdo de imagem → gera HTML com <img>
                html = self._parse_image_to_html(response_data, gopher_type)
            else:
                # Conteúdo textual/menu → converte mapa Gopher em HTML
                gopher_map = response_data.decode('utf-8', errors='ignore')
                html = self._parse_gopher_map_to_html(gopher_map, host, port)

            tab.setHtml(html, QUrl(url))

        except Exception as e:
            print(f"Erro ao acessar Gopher: {e}")
            tab.setHtml(f"<h1>Erro ao acessar Gopher</h1><p>{e}</p>")

    def _parse_image_to_html(self, image_data, gopher_type):
        """
        Converte dados brutos de imagem em uma página HTML com a imagem embutida.

        - Suporta GIF (g), JPEG (I) e PNG (p).
        - Codifica os bytes da imagem em Base64.
        - Retorna HTML com <img> centralizado e fundo escuro.
        """
        mime_map = {'g': 'image/gif', 'p': 'image/png', 'I': 'image/jpeg'}
        mime_type = mime_map.get(gopher_type, 'application/octet-stream')

        b64_data = base64.b64encode(image_data).decode('ascii')

        return (
            f'<html><body style="background-color: #333; display: grid; '
            f'place-items: center; margin: 0;">'
            f'<img src="data:{mime_type};base64,{b64_data}"></body></html>'
        )

    def _parse_gopher_map_to_html(self, gopher_map, current_host, current_port):
        """
        Converte um mapa Gopher (texto estruturado) em HTML navegável.

        - Cada linha do mapa representa um item (arquivo, diretório, link, etc.).
        - Interpreta o tipo do item (primeiro caractere da linha).
        - Gera links HTML apropriados para cada tipo:
            - '0' → Documento de texto
            - '1' → Diretório
            - 'h' → Link externo (HTTP/HTML)
            - 'g', 'I', 'p' → Imagens
            - 'i' → Informação (texto simples)
            - Outros → Exibe como desconhecido
        - Retorna HTML estilizado com <pre> e ícones visuais.
        """
        html_lines = [
            '<html><head><meta charset="UTF-8">',
            '<title>Gopher Page</title>',
            '<style>body { font-family: monospace; background-color: #f0f0f0; '
            'color: #333; } a { text-decoration: none; color: #0000FF;} '
            'p { margin: 2px; }</style>',
            '</head><body><h2>Gopherspace</h2><pre>'
        ]

        for line in gopher_map.splitlines():
            if not line or len(line) < 2:
                continue

            item_type = line[0]
            parts = line[1:].split('\t')
            display_text = parts[0]
            selector = parts[1] if len(parts) > 1 else ""
            host = parts[2] if len(parts) > 2 else current_host
            port = parts[3] if len(parts) > 3 else current_port

            if item_type == 'i':
                html_lines.append(f'<p>  {display_text}</p>')
            elif item_type == '0':
                html_lines.append(
                    f'<p>📄 <a href="gopher://{host}:{port}{selector}?gopher_type=0">'
                    f'{display_text}</a></p>'
                )
            elif item_type == '1':
                html_lines.append(
                    f'<p>📁 <a href="gopher://{host}:{port}{selector}?gopher_type=1">'
                    f'{display_text}</a></p>'
                )
            elif item_type == 'h':
                html_url = selector.replace("URL:", "")
                html_lines.append(f'<p>🌐 <a href="{html_url}">{display_text}</a></p>')
            elif item_type in ('g', 'I', 'p'):  # GIF, JPEG, PNG
                html_lines.append(
                    f'<p>🖼️ <a href="gopher://{host}:{port}{selector}?gopher_type={item_type}">'
                    f'{display_text}</a></p>'
                )
            else:
                html_lines.append(
                    f'<p>❓ <a href="gopher://{host}:{port}{selector}?gopher_type={item_type}">'
                    f'{display_text}</a> (Tipo {item_type})</p>'
                )

        html_lines.append('</pre></body></html>')
        return "".join(html_lines)