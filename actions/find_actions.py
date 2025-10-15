# actions/find_actions.py

"""
Este módulo contém o mixin FindActions, responsável pela funcionalidade
de "Procurar na Página".

A classe implementa a lógica para abrir e fechar a barra de ferramentas de busca,
bem como para executar buscas progressivas (próximo/anterior) em diferentes
tipos de conteúdo, como WebViews e editores de texto.
"""

# --- Imports de Terceiros (PySide6) ---
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtGui import QTextDocument

# --- Imports Locais da Aplicação ---
# As classes de componentes são necessárias para a verificação de tipo (isinstance).
from components import WebView, HtmlEditor, SplitEditor
# QPlainTextEdit é importado diretamente pois é uma classe base usada para verificação.
from PySide6.QtWidgets import QPlainTextEdit


class FindActions:
    """
    Classe responsável pelas ações de busca de texto no navegador/editor.

    Permite abrir/fechar a barra de busca, localizar texto na aba atual
    (seja em páginas web ou editores de texto) e navegar entre as ocorrências.
    """

    def abrir_busca(self):
        """
        Exibe a barra de busca e coloca o foco no campo de entrada.

        - Torna a barra de busca visível.
        - Garante que o usuário possa digitar imediatamente o termo a ser buscado.
        """
        self.find_toolbar.show()
        self.find_input.setFocus()

    def fechar_busca(self):
        """
        Fecha a barra de busca e limpa os destaques de pesquisa.

        - Oculta a barra de busca.
        - Se a aba atual for uma WebView, limpa os resultados da busca.
        - Se for um editor de texto (HtmlEditor ou QPlainTextEdit),
          remove a seleção atual do cursor.
        """
        self.find_toolbar.hide()
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            aba.findText("")  # limpa destaques
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            cursor = aba.textCursor()
            cursor.clearSelection()
            aba.setTextCursor(cursor)

    def buscar_texto(self, text):
        """
        Realiza a busca inicial do texto informado na aba atual.

        - Em WebView: usa o método `findText` do QWebEnginePage.
        - Em editores de texto: posiciona o cursor no início do documento
          e executa a busca pelo termo.
        """
        aba = self.aba_atual()
        if isinstance(aba, WebView):
            aba.findText(text)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            cursor = aba.textCursor()
            cursor.setPosition(0)  # início do documento
            aba.setTextCursor(cursor)
            aba.find(text)

    def buscar_proximo(self):
        """
        Busca a próxima ocorrência do termo digitado.

        - Obtém o texto do campo de busca.
        - Em WebView: chama `findText` novamente para avançar.
        - Em editores de texto: usa `find` para localizar a próxima ocorrência.
        """
        aba = self.aba_atual()
        text = self.find_input.text()
        if isinstance(aba, WebView):
            aba.findText(text)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            aba.find(text)

    def buscar_anterior(self):
        """
        Busca a ocorrência anterior do termo digitado.

        - Obtém o texto do campo de busca.
        - Em WebView: usa a flag `FindBackward` do QWebEnginePage.
        - Em editores de texto: usa a flag `FindBackward` do QTextDocument.
        """
        aba = self.aba_atual()
        text = self.find_input.text()
        if isinstance(aba, WebView):
            aba.findText(text, QWebEnginePage.FindFlag.FindBackward)
        elif isinstance(aba, (HtmlEditor, QPlainTextEdit)):
            aba.find(text, QTextDocument.FindFlag.FindBackward)