"""
Processador de vídeo para detecção de gestos.
"""

import cv2
import threading
import time
from typing import Callable, Optional
import mediapipe as mp
from src.gesture_detector.gesture_detector import GestureDetector
from src.config.config import Config


class VideoProcessor:
    """Processa vídeo da câmera e detecta gestos."""
    
    def __init__(self, camera_index: int = None, callback_gesto: Optional[Callable] = None, callback_frame: Optional[Callable] = None, callback_mao_aberta: Optional[Callable] = None, callback_mao_fechada: Optional[Callable] = None):
        """
        Inicializa o processador de vídeo.
        
        Args:
            camera_index: Índice da câmera (padrão: 0).
            callback_gesto: Função chamada quando um gesto é detectado.
                            Recebe (chave, dedos_estendidos, indice_mao) como argumentos.
            callback_frame: Função chamada para cada frame processado.
                            Recebe (frame_bgr) como argumento.
            callback_mao_aberta: Função chamada quando mão totalmente aberta é detectada (confirmação/envio).
            callback_mao_fechada: Função chamada quando mão fechada é detectada (cancelamento).
        """
        self.camera_index = camera_index or Config.CAMERA_INDEX
        self.callback_gesto = callback_gesto
        self.callback_frame = callback_frame
        self.callback_mao_aberta = callback_mao_aberta
        self.callback_mao_fechada = callback_mao_fechada
        self.cap: Optional[cv2.VideoCapture] = None
        self.detector = GestureDetector()
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.show_opencv_window = Config.SHOW_OPENCV_WINDOW
        self.ultimo_gesto_detectado = None  # Armazena último gesto para envio com mão aberta
        
        # Estado de aguardando confirmação (controlado externamente)
        self.aguardando_confirmacao = False
        
        # Debounce para evitar múltiplas chamadas do callback com o mesmo gesto
        self.ultimo_gesto_chamado = None  # Último gesto que chamou o callback
        self.ultimo_tempo_callback = 0  # Timestamp da última chamada do callback
        self.DEBOUNCE_CALLBACK_SEGUNDOS = 0.5  # Aguarda 0.5s antes de chamar callback novamente com o mesmo gesto
        
        # Debounce para detecção de mão fechada (cancelamento)
        self.ultimo_tempo_mao_fechada = 0  # Timestamp da última detecção de mão fechada
        self.DEBOUNCE_MAO_FECHADA_SEGUNDOS = 0.3  # Aguarda 0.3s antes de detectar mão fechada novamente
        
        # Debounce para detecção de mão totalmente aberta (confirmação)
        self.ultimo_tempo_mao_aberta = 0  # Timestamp da última detecção de mão aberta
        self.DEBOUNCE_MAO_ABERTA_SEGUNDOS = 0.5  # Aguarda 0.5s antes de detectar mão aberta novamente
    
    def iniciar(self):
        """Inicia a captura de vídeo."""
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"Não foi possível abrir a câmera {self.camera_index}")
        
        self.running = True
        self.thread = threading.Thread(target=self._loop_video, daemon=True)
        self.thread.start()
    
    def _loop_video(self):
        """Loop principal de processamento de vídeo."""
        while self.running:
            if self.cap is None:
                break
            
            success, img = self.cap.read()
            if not success:
                break
            
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            result = self.detector.processar_frame(img_rgb)
            
            if result.multi_hand_landmarks:
                for idx, hand_landmarks in enumerate(result.multi_hand_landmarks):
                    # Desenha landmarks na imagem
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )
                    
                    # CRÍTICO: Verifica mão totalmente aberta ANTES de processar como gesto normal
                    # Mão totalmente aberta (todos os 5 dedos) = confirmação/envio
                    # NÃO deve ser tratada como gesto válido, apenas para confirmação
                    is_mao_aberta = self.detector.detectar_mao_totalmente_aberta(hand_landmarks.landmark)
                    
                    if is_mao_aberta:
                        # Mão totalmente aberta detectada - usado APENAS para confirmação/envio
                        # NÃO processa como gesto normal e NÃO armazena como gesto detectado
                        
                        # Debounce: evita múltiplas detecções de mão aberta
                        tempo_atual = time.time()
                        tempo_suficiente_mao_aberta = tempo_atual - self.ultimo_tempo_mao_aberta >= self.DEBOUNCE_MAO_ABERTA_SEGUNDOS
                        
                        # Chama callback de confirmação apenas se estiver aguardando confirmação e passou tempo suficiente
                        if self.callback_mao_aberta and self.aguardando_confirmacao:
                            if tempo_suficiente_mao_aberta:
                                # Passa None como gesto_info - o callback do main.py usará ultimo_gesto_valido
                                print(f"✅ Mão totalmente aberta detectada! Confirmando envio...")
                                self.callback_mao_aberta(None)  # Passa None, o callback usa ultimo_gesto_valido do main.py
                                self.ultimo_tempo_mao_aberta = tempo_atual
                            else:
                                # Está aguardando mas ainda não passou tempo suficiente (debounce)
                                # Não loga para evitar spam no console
                                pass
                        elif not self.aguardando_confirmacao:
                            # Apenas loga se não estiver aguardando (para não poluir o console)
                            pass
                        
                        # Exibe informação na imagem
                        texto = f"Mão {idx+1}: 🖐️ MÃO ABERTA"
                        if self.aguardando_confirmacao:
                            texto += " (Confirmando...)"
                        else:
                            texto += " (Faça um gesto primeiro)"
                        cv2.putText(
                            img,
                            texto,
                            (10, 70 + idx * 30),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            1,
                            (0, 255, 0),  # Verde para mão aberta
                            2
                        )
                        # PULA processamento como gesto normal quando é mão totalmente aberta
                        continue
                    
                    # Detecta gesto normal (apenas se NÃO for mão totalmente aberta)
                    chave, dedos_estendidos = self.detector.detectar_gesto(
                        hand_landmarks.landmark
                    )
                    
                    # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20) mesmo que detectada como gesto normal
                    # Isso garante que mão totalmente aberta nunca seja tratada como um gesto reconhecido
                    # Mão totalmente aberta = confirmação/envio, não é um gesto válido
                    if chave == (4, 8, 12, 16, 20):
                        continue
                    
                    # CRÍTICO: Verifica se é mão fechada (nenhum dedo estendido = cancelamento)
                    # Mão fechada NUNCA deve ser tratada como gesto válido, apenas para cancelamento
                    if not chave or len(chave) == 0:
                        # Mão fechada detectada - usado APENAS para cancelar envio
                        # Só cancela se estiver aguardando confirmação e passou tempo suficiente
                        tempo_atual = time.time()
                        tempo_suficiente_mao_fechada = tempo_atual - self.ultimo_tempo_mao_fechada >= self.DEBOUNCE_MAO_FECHADA_SEGUNDOS
                        
                        if self.callback_mao_fechada and self.aguardando_confirmacao and tempo_suficiente_mao_fechada:
                            print("✊ Mão fechada detectada! Cancelando envio...")
                            self.callback_mao_fechada()
                            self.ultimo_tempo_mao_fechada = tempo_atual
                        # IMPORTANTE: Mão fechada NUNCA é armazenada como gesto detectado
                        # Continue sempre para ignorar completamente o processamento como gesto normal
                        continue
                    
                    # NOVO FLUXO: Se estiver aguardando confirmação, ignora novos gestos
                    # Só processa novos gestos após confirmação (joia) ou cancelamento (mão fechada)
                    if self.aguardando_confirmacao:
                        continue  # Ignora novos gestos enquanto aguarda confirmação
                    
                    # Armazena último gesto detectado (apenas gestos válidos, não joia)
                    # O callback de gesto será responsável por validar se tem mensagem antes de armazenar
                    self.ultimo_gesto_detectado = (chave, dedos_estendidos, idx)
                    
                    # Debounce: evita chamar callback repetidamente com o mesmo gesto
                    tempo_atual = time.time()
                    gesto_mudou = self.ultimo_gesto_chamado != chave
                    tempo_suficiente = tempo_atual - self.ultimo_tempo_callback >= self.DEBOUNCE_CALLBACK_SEGUNDOS
                    
                    # Só chama callback se o gesto mudou ou passou tempo suficiente
                    if self.callback_gesto and (gesto_mudou or tempo_suficiente):
                        self.callback_gesto(chave, dedos_estendidos, idx)
                        self.ultimo_gesto_chamado = chave
                        self.ultimo_tempo_callback = tempo_atual
                    
                    # Exibe informação na imagem
                    texto = f"Mão {idx+1}: {chave}"
                    cv2.putText(
                        img,
                        texto,
                        (10, 70 + idx * 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2
                    )
            
            # Chama callback de frame se fornecido (para exibir na UI)
            if self.callback_frame:
                try:
                    self.callback_frame(img.copy())
                except Exception as e:
                    print(f"Erro ao chamar callback de frame: {e}")
            
            # Mostra janela OpenCV apenas se configurado
            if self.show_opencv_window:
                cv2.imshow("Detecção de Gestos", img)
                
                # Verifica se ESC foi pressionado
                if cv2.waitKey(1) & 0xFF == 27:
                    self.parar()
                    break
            else:
                # Pequeno delay para não sobrecarregar CPU
                import time
                time.sleep(1.0 / Config.VIDEO_FPS)
    
    def parar(self):
        """Para a captura de vídeo e libera recursos."""
        self.running = False
        
        if self.cap:
            self.cap.release()
        
        if self.show_opencv_window:
            cv2.destroyAllWindows()
        self.detector.liberar()
    
    def aguardar_finalizacao(self):
        """Aguarda a thread de vídeo finalizar."""
        if self.thread and self.thread.is_alive():
            self.thread.join()

