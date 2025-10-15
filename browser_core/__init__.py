# browser_core/__init__.py

# Exporta todas as classes de mixin do núcleo do navegador para que possam ser
# importadas de forma centralizada a partir do pacote 'browser_core'.
from .ui_builder import UIBuilderMixin
from .tab_manager import TabManagerMixin
from .event_handlers import EventHandlersMixin