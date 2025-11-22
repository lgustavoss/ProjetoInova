"""
ProjetoInova - Sistema de Reconhecimento de Gestos
Ponto de entrada principal da aplicação.
"""

import sys
import threading
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, str(Path(__file__).parent))

from src.ui.main_window import MainWindow
from src.video.video_processor import VideoProcessor
from src.data.gesto_repository import GestoRepository
from src.audio.audio_handler import AudioHandler
from src.websocket.websocket_server import WebSocketServer
from src.config.config import Config


def main():
    """Função principal da aplicação."""
    websocket_server = None
    
    try:
        # Inicializa componentes
        repositorio = GestoRepository()
        audio_handler = AudioHandler()
        janela = MainWindow()
        
        # Inicializa servidor WebSocket se habilitado
        if Config.WEBSOCKET_ENABLED:
            try:
                websocket_server = WebSocketServer(
                    host=Config.WEBSOCKET_HOST,
                    port=Config.WEBSOCKET_PORT
                )
                thread_websocket = threading.Thread(
                    target=websocket_server.iniciar,
                    daemon=True
                )
                thread_websocket.start()
                print(f"✅ WebSocket habilitado. Enfermeiros podem conectar em ws://{Config.WEBSOCKET_HOST}:{Config.WEBSOCKET_PORT}")
            except Exception as e:
                print(f"⚠️ Erro ao iniciar WebSocket: {e}")
                print("   Aplicação continuará sem WebSocket.")
                websocket_server = None
        
        # Callback para frames de vídeo (atualiza interface)
        def on_frame_processado(frame_bgr):
            """Callback chamado para cada frame processado."""
            janela.atualizar_frame_video(frame_bgr)
        
        # Callback para quando um gesto é detectado (apenas mostra, não envia)
        def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
            mensagem = repositorio.obter_mensagem(chave)
            
            if mensagem:
                mensagem_exibida = mensagem
            else:
                mensagem_exibida = f"Gesto não reconhecido: {chave}"
            
            # Atualiza interface e pede confirmação (não envia automaticamente)
            janela.atualizar_gesto_atual(chave, mensagem_exibida)
        
        # Callback para enviar gesto confirmado pelo paciente
        def on_enviar_gesto_confirmado(chave, mensagem):
            """Envia gesto confirmado pelo paciente via WebSocket."""
            if websocket_server:
                prioridade = "alta" if audio_handler.verificar_mensagem_critica(mensagem) else "normal"
                websocket_server.broadcast({
                    "tipo": "gesto",
                    "paciente": f"{Config.PACIENTE_NOME} - Quarto {Config.PACIENTE_QUARTO}",
                    "mensagem": mensagem,
                    "prioridade": prioridade,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                print(f"📤 Gesto enviado: {mensagem} (Prioridade: {prioridade})")
        
        # Configura callback de envio na janela
        janela.callback_enviar_gesto = on_enviar_gesto_confirmado
        
        # Inicializa processador de vídeo
        processador_video = VideoProcessor(
            callback_gesto=on_gesto_detectado,
            callback_frame=on_frame_processado
        )
        processador_video.iniciar()
        
        # Executa interface gráfica
        janela.executar()
        
        # Limpa recursos ao fechar
        processador_video.parar()
        if websocket_server:
            websocket_server.parar()
        
    except KeyboardInterrupt:
        print("\nAplicação interrompida pelo usuário.")
    except Exception as e:
        print(f"Erro ao executar aplicação: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
