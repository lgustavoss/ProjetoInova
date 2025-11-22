"""
Configurações da aplicação.
"""

import os
from pathlib import Path


class Config:
    """Gerencia as configurações da aplicação."""
    
    # Diretórios
    BASE_DIR = Path(__file__).parent.parent.parent
    DATA_DIR = BASE_DIR
    
    # Arquivos
    CSV_PATH = DATA_DIR / 'dados.csv'
    EXPORT_PATH = DATA_DIR / 'gestos_exportados.txt'
    ALERT_SOUND_PATH = DATA_DIR / 'alerta.mp3'
    
    # Configurações de vídeo
    CAMERA_INDEX = 0
    
    # Configurações de reconhecimento de voz
    LANGUAGE = 'pt-BR'
    
    # Configurações da interface
    WINDOW_TITLE = "Painel do Paciente - Reconhecimento de Gestos"
    WINDOW_SIZE = "1000x700"
    FONT_FAMILY = "Arial"
    FONT_SIZE_NORMAL = 12
    FONT_SIZE_LARGE = 14
    FONT_SIZE_XLARGE = 16
    
    # Configurações de vídeo na interface
    VIDEO_WIDTH = 640
    VIDEO_HEIGHT = 480
    VIDEO_FPS = 30
    
    # Mostrar janela OpenCV separada (False = apenas na interface Tkinter)
    SHOW_OPENCV_WINDOW = False
    
    # Palavras-chave para alertas críticos
    CRITICAL_KEYWORDS = ['emergência', 'pânico', 'urgente']
    
    # Configurações WebSocket
    WEBSOCKET_ENABLED = True
    WEBSOCKET_HOST = "localhost"
    WEBSOCKET_PORT = 8765
    
    # Informações do paciente (configurar conforme necessário)
    PACIENTE_ID = "PAC001"
    PACIENTE_NOME = "João Silva"
    PACIENTE_QUARTO = "201"
    
    # Gesto de confirmação/envio (joia = polegar + indicador formando círculo)
    # Representado como (4, 8) - polegar e indicador
    GESTO_JOIA_CONFIRMACAO = (4, 8)
    
    # Debounce para evitar envios múltiplos do mesmo gesto
    DEBOUNCE_TEMPO_SEGUNDOS = 2  # Aguarda 2 segundos antes de aceitar o mesmo gesto novamente
    
    @classmethod
    def ensure_data_file_exists(cls):
        """Garante que o arquivo CSV existe."""
        if not cls.CSV_PATH.exists():
            cls.CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CSV_PATH, 'w', encoding='utf-8') as f:
                f.write('dedos,mensagem\n')

