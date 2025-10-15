# actions/ai_actions.py

"""
Este módulo encapsula toda a lógica relacionada com a integração do assistente
de Inteligência Artificial (IA) no navegador.

Contém o mixin AIActions, que orquestra o processo, e a classe WorkerIA,
que executa as chamadas de API de forma assíncrona para não bloquear a interface.
"""

# --- Imports de Terceiros ---
import google.generativeai as genai
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtWidgets import QInputDialog

# --- Imports Locais da Aplicação ---
from components import WebView

class WorkerIA(QObject):
    """
    Worker responsável por executar chamadas à API de IA em uma thread separada.

    Responsabilidades:
    - Configurar e chamar o modelo de IA (Gemini).
    - Emitir sinais com o resultado, erro ou término da execução.
    - Garantir que a interface gráfica (UI) permaneça responsiva durante a chamada.
    """

    # --- Sinais Qt ---
    resultado_pronto = Signal(str)   # Emitido quando a resposta da IA está disponível
    erro_ocorrido = Signal(str)      # Emitido em caso de erro na chamada da API
    finished = Signal()              # Emitido quando a execução é concluída (com ou sem sucesso)

    def __init__(self, api_key, prompt):
        """
        Inicializa o worker com a chave da API e o prompt a ser enviado.

        :param api_key: Chave de autenticação para a API do Gemini.
        :param prompt: Texto de entrada (instrução ou pergunta) a ser enviado ao modelo.
        """
        super().__init__()
        self.api_key = api_key
        self.prompt = prompt

    def rodar(self):
        """
        Executa a chamada à API do Gemini em uma thread separada.

        - Configura a biblioteca `genai` com a chave da API.
        - Cria uma instância do modelo `gemini-2.5-flash`.
        - Envia o prompt e aguarda a resposta.
        - Emite o sinal `resultado_pronto` com o texto retornado.
        - Em caso de erro, emite `erro_ocorrido` com a mensagem de exceção.
        - Sempre emite `finished` ao final, garantindo que a thread seja liberada.
        """
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(self.prompt)

            # Emite o resultado para ser tratado pela UI
            self.resultado_pronto.emit(response.text)

        except Exception as e:
            # Emite erro para ser exibido/logado pela aplicação
            self.erro_ocorrido.emit(f"Erro na API do Gemini: {e}")

        finally:
            # Garante que a thread seja finalizada corretamente
            self.finished.emit()

class AIActions:
    """
    Mixin para as ações de Inteligência Artificial.

    Responsabilidades:
    - Gerenciar a chave de API do Gemini (solicitar ao usuário, salvar e reutilizar).
    - Criar e iniciar threads para execução de prompts de IA sem travar a interface.
    - Integrar os resultados da IA ao painel de assistente (ai_panel).
    """

    def processar_prompt_ia(self, prompt):
        """
        Processa um prompt de IA fornecido pelo usuário.

        Fluxo:
        1. Verifica se a chave de API está configurada.
           - Caso não esteja, solicita ao usuário via diálogo.
           - Se o usuário fornecer, salva a chave para uso futuro.
           - Se não fornecer, cancela a operação e informa no painel de IA.
        2. Se a chave estiver disponível, cria uma thread dedicada.
        3. Instancia um WorkerIA com a chave e o prompt.
        4. Conecta sinais do worker para:
            - Exibir resposta no painel de IA.
            - Exibir erros no painel de IA.
            - Encerrar e limpar a thread ao término.
        5. Inicia a execução da thread.
        """
        if not self.api_key:
            texto, ok = QInputDialog.getText(
                self,
                "Chave de API do Gemini",
                "Por favor, insira sua chave de API do Google AI Studio:"
            )
            if ok and texto:
                self.api_key = texto.strip()
                self.salvar_config()  # Persiste a chave para próximas execuções
            else:
                self.ai_panel.set_response(
                    "Operação cancelada. A chave de API é necessária para usar o assistente."
                )
                return

        if not self.api_key:
            return

        # Criação da thread e do worker
        self.thread = QThread()
        self.worker = WorkerIA(self.api_key, prompt)
        self.worker.moveToThread(self.thread)

        # Conexão de sinais
        self.thread.started.connect(self.worker.rodar)
        self.worker.resultado_pronto.connect(self.ai_panel.set_response)
        self.worker.erro_ocorrido.connect(self.ai_panel.set_response)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Inicia a thread
        self.thread.start()

    def _iniciar_worker_ia_com_contexto(self, page_text, original_prompt):
        """
        Cria o prompt final com base no contexto da página e inicia o worker de IA.

        - Recebe o texto da página e o prompt original do usuário.
        - Se houver texto da página:
            - Limita o conteúdo a 15.000 caracteres (para evitar excesso de dados).
            - Constrói um prompt contextualizado, instruindo a IA a responder
              exclusivamente com base no conteúdo fornecido.
        - Cria e inicia uma thread com WorkerIA, de forma idêntica ao método anterior.
        """
        final_prompt = original_prompt

        if page_text:
            page_text = page_text[:15000]  # Limita tamanho do contexto
            final_prompt = f"""Com base EXCLUSIVAMENTE no seguinte texto de uma página da web:

'''
{page_text}
'''

Responda ao seguinte pedido do usuário: "{original_prompt}"
"""

        # Criação da thread e do worker com prompt contextualizado
        self.thread = QThread()
        self.worker = WorkerIA(self.api_key, final_prompt)
        self.worker.moveToThread(self.thread)

        # Conexão de sinais
        self.thread.started.connect(self.worker.rodar)
        self.worker.resultado_pronto.connect(self.ai_panel.set_response)
        self.worker.erro_ocorrido.connect(self.ai_panel.set_response)
        self.worker.finished.connect(self.thread.quit)
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # Inicia a thread
        self.thread.start()