"""
ProjetoInova - Sistema de Reconhecimento de Gestos
Ponto de entrada principal da aplicação.
"""

import sys
import threading
import time
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
    ultimo_gesto_enviado = None
    ultimo_tempo_envio = 0
    
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
                # Aguarda um pouco para o servidor iniciar
                time.sleep(0.5)
                print(f"✅ WebSocket habilitado. Enfermeiros podem conectar em ws://{Config.WEBSOCKET_HOST}:{Config.WEBSOCKET_PORT}")
                print(f"📱 Abra o arquivo 'cliente_enfermeiro.html' no navegador")
            except Exception as e:
                print(f"⚠️ Erro ao iniciar WebSocket: {e}")
                import traceback
                traceback.print_exc()
                print("   Aplicação continuará sem WebSocket.")
                websocket_server = None
        
        # Callback para frames de vídeo (atualiza interface)
        def on_frame_processado(frame_bgr):
            """Callback chamado para cada frame processado."""
            janela.atualizar_frame_video(frame_bgr)
        
        # Variáveis para controle de gestos e estado
        ultimo_gesto_valido = None  # Último gesto válido armazenado para envio
        aguardando_confirmacao = False  # Estado de espera por confirmação ou cancelamento
        
        # Callback para quando um gesto é detectado
        def on_gesto_detectado(chave, dedos_estendidos, indice_mao):
            nonlocal ultimo_gesto_valido, aguardando_confirmacao
            
            # CRÍTICO: Ignora gestos vazios (mão fechada) - usado APENAS para cancelamento
            # Mão fechada nunca deve ser tratada como gesto válido
            if not chave or len(chave) == 0:
                return
            
            # Valida que todos os índices são válidos (4, 8, 12, 16, 20)
            # Ignora gestos com índices inválidos (como 0)
            indices_validos = {4, 8, 12, 16, 20}
            if not all(d in indices_validos for d in chave):
                return  # Ignora gestos com índices inválidos
            
            # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20) - usada APENAS para confirmação/envio
            # Mão totalmente aberta nunca deve ser tratada como gesto válido
            if chave == (4, 8, 12, 16, 20):
                return
            
            # Se já estiver aguardando confirmação, ignora novos gestos
            if aguardando_confirmacao:
                return
            
            mensagem = repositorio.obter_mensagem(chave)
            
            if mensagem:
                # Armazena gesto válido
                ultimo_gesto_valido = (chave, dedos_estendidos, indice_mao)
                
                # Ativa estado de aguardando confirmação
                aguardando_confirmacao = True
                processador_video.aguardando_confirmacao = True
                
                # Mostra gesto detectado e solicita confirmação
                mensagem_exibida = f"✅ Gesto Detectado!\n\n{mensagem}\n\n🖐️ Abra a mão totalmente para enviar\n✊ Feche a mão para cancelar"
                janela.atualizar_gesto_atual(chave, mensagem_exibida)
                
                print(f"📝 Gesto detectado: {chave} = {mensagem}")
                print("⏳ Aguardando confirmação... (🖐️ mão aberta para enviar ou ✊ mão fechada para cancelar)")
            else:
                # Gesto não reconhecido - não entra em modo de espera
                mensagem_exibida = f"⚠️ Gesto não reconhecido: {chave}\n\nTente fazer um gesto válido."
                janela.atualizar_gesto_atual(chave, mensagem_exibida)
                print(f"⚠️ Gesto não reconhecido: {chave}")
        
        # Variáveis para controle de envio
        ultimo_gesto_enviado = None
        ultimo_tempo_envio = 0
        
        # Função auxiliar para restaurar estado padrão após enviar/cancelar
        def restaurar_estado_padrao():
            """Restaura o estado padrão da interface após enviar ou cancelar."""
            nonlocal aguardando_confirmacao
            aguardando_confirmacao = False
            processador_video.aguardando_confirmacao = False
            # O método _restaurar_status_padrao será chamado automaticamente após a mensagem temporária
        
        # Callback para mão fechada (cancelamento)
        def on_mao_fechada_detectada():
            """Cancela o envio e volta a detectar novos gestos."""
            nonlocal aguardando_confirmacao, ultimo_gesto_valido
            
            if aguardando_confirmacao:
                # Cancela e volta ao estado inicial
                aguardando_confirmacao = False
                processador_video.aguardando_confirmacao = False
                ultimo_gesto_valido = None
                
                # Mostra feedback de cancelamento
                janela.mostrar_mensagem_temporaria("❌ Envio cancelado\n\nVocê pode fazer um novo gesto.", "aviso", duracao_segundos=3)
                print("❌ Envio cancelado. Aguardando novo gesto...")
                
                # Restaura estado padrão após exibir mensagem
                janela.root.after(3500, restaurar_estado_padrao)
        
        # Callback para mão totalmente aberta (confirmação/envio)
        def on_mao_aberta_detectada(gesto_info):
            """Envia o gesto quando mão totalmente aberta é detectada durante aguardando confirmação."""
            nonlocal ultimo_gesto_enviado, ultimo_tempo_envio, ultimo_gesto_valido, aguardando_confirmacao
            
            # Só processa se estiver aguardando confirmação
            if not aguardando_confirmacao:
                return
            
            if not ultimo_gesto_valido:
                print("⚠️ Mão totalmente aberta detectada, mas nenhum gesto válido foi armazenado.")
                return
            
            chave, dedos_estendidos, indice_mao = ultimo_gesto_valido
            mensagem = repositorio.obter_mensagem(chave)
            
            if not mensagem:
                print(f"⚠️ Erro: gesto {chave} não tem mensagem associada.")
                return
            
            # Debounce: evita envios múltiplos do mesmo gesto
            tempo_atual = time.time()
            if (ultimo_gesto_enviado == chave and 
                tempo_atual - ultimo_tempo_envio < Config.DEBOUNCE_TEMPO_SEGUNDOS):
                return
            
            # Envia via WebSocket
            if websocket_server and websocket_server.running:
                prioridade = "alta" if audio_handler.verificar_mensagem_critica(mensagem) else "normal"
                websocket_server.broadcast({
                    "tipo": "gesto",
                    "paciente": f"{Config.PACIENTE_NOME} - Quarto {Config.PACIENTE_QUARTO}",
                    "mensagem": mensagem,
                    "prioridade": prioridade,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                # Atualiza controle de debounce
                ultimo_gesto_enviado = chave
                ultimo_tempo_envio = tempo_atual
                
                # Desativa estado de aguardando confirmação
                aguardando_confirmacao = False
                processador_video.aguardando_confirmacao = False
                ultimo_gesto_valido = None
                
                # Feedback visual de sucesso
                emoji_prioridade = "🔴" if prioridade == "alta" else "✅"
                mensagem_feedback = f"{emoji_prioridade} MENSAGEM ENVIADA COM SUCESSO!\n\n{mensagem}\n\n👍 O enfermeiro foi notificado"
                janela.mostrar_mensagem_temporaria(mensagem_feedback, "sucesso", duracao_segundos=5)
                
                # Restaura estado padrão após exibir mensagem
                janela.root.after(5500, restaurar_estado_padrao)
                
                print(f"📤 Gesto enviado: {mensagem} (Prioridade: {prioridade})")
                print("✅ Estado resetado. Aguardando novo gesto...")
            else:
                janela.mostrar_mensagem_temporaria("⚠️ WebSocket não conectado. Verifique a conexão.", "erro", duracao_segundos=3)
                print("⚠️ WebSocket não está rodando. Não foi possível enviar.")
        
        # Inicializa processador de vídeo
        processador_video = VideoProcessor(
            callback_gesto=on_gesto_detectado,
            callback_frame=on_frame_processado,
            callback_mao_aberta=on_mao_aberta_detectada,
            callback_mao_fechada=on_mao_fechada_detectada
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
