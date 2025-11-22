"""
Processador de vídeo para detecção de gestos.
"""

import cv2
import threading
from typing import Callable, Optional
import mediapipe as mp
from src.gesture_detector.gesture_detector import GestureDetector
from src.config.config import Config


class VideoProcessor:
    """Processa vídeo da câmera e detecta gestos."""
    
    def __init__(self, camera_index: int = None, callback_gesto: Optional[Callable] = None):
        """
        Inicializa o processador de vídeo.
        
        Args:
            camera_index: Índice da câmera (padrão: 0).
            callback_gesto: Função chamada quando um gesto é detectado.
                            Recebe (chave, mensagem, indice_mao) como argumentos.
        """
        self.camera_index = camera_index or Config.CAMERA_INDEX
        self.callback_gesto = callback_gesto
        self.cap: Optional[cv2.VideoCapture] = None
        self.detector = GestureDetector()
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_hands = mp.solutions.hands
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
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
                    
                    # Detecta gesto
                    chave, dedos_estendidos = self.detector.detectar_gesto(
                        hand_landmarks.landmark
                    )
                    
                    # Chama callback se fornecido
                    if self.callback_gesto:
                        self.callback_gesto(chave, dedos_estendidos, idx)
                    
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
            
            cv2.imshow("Detecção de Gestos", img)
            
            # Verifica se ESC foi pressionado
            if cv2.waitKey(1) & 0xFF == 27:
                self.parar()
                break
    
    def parar(self):
        """Para a captura de vídeo e libera recursos."""
        self.running = False
        
        if self.cap:
            self.cap.release()
        
        cv2.destroyAllWindows()
        self.detector.liberar()
    
    def aguardar_finalizacao(self):
        """Aguarda a thread de vídeo finalizar."""
        if self.thread and self.thread.is_alive():
            self.thread.join()

