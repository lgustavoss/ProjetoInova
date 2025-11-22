"""
Detector de gestos usando MediaPipe.
"""

import math
from typing import Tuple, List, Optional
import mediapipe as mp


class GestureDetector:
    """Detecta gestos de mão usando MediaPipe."""
    
    # Índices dos dedos no MediaPipe
    INDICES_DEDOS = {
        'polegar': 4,
        'indicador': 8,
        'medio': 12,
        'anelar': 16,
        'mindinho': 20
    }
    
    # Pontos de referência para cada dedo
    PONTOS_REFERENCIA = {
        8: 6,   # Indicador
        12: 10, # Médio
        16: 14, # Anelar
        20: 18  # Mindinho
    }
    
    def __init__(self):
        """Inicializa o detector de gestos."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
    
    def detectar_dedos_estendidos(self, landmarks) -> List[int]:
        """
        Detecta quais dedos estão estendidos.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            Lista de índices dos dedos estendidos.
        """
        dedos_estendidos = []
        
        # Verifica dedos (exceto polegar)
        for dedo_topo, dedo_base in self.PONTOS_REFERENCIA.items():
            if landmarks[dedo_topo].y < landmarks[dedo_base].y:
                dedos_estendidos.append(dedo_topo)
        
        # Verifica polegar (lógica diferente - comparação horizontal)
        if landmarks[4].x < landmarks[3].x:
            dedos_estendidos.append(4)
        
        return dedos_estendidos
    
    def detectar_gesto_joia(self, landmarks) -> bool:
        """
        Detecta se o gesto é "joia" (polegar e indicador formando círculo).
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            True se for gesto joia, False caso contrário.
        """
        try:
            # Pontos do polegar e indicador
            thumb_tip = landmarks[4]  # Polegar ponta
            thumb_ip = landmarks[3]   # Polegar articulação
            index_tip = landmarks[8]  # Indicador ponta
            index_pip = landmarks[6]  # Indicador articulação
            
            # Calcula distância entre ponta do polegar e ponta do indicador
            distancia = math.sqrt(
                (thumb_tip.x - index_tip.x) ** 2 + 
                (thumb_tip.y - index_tip.y) ** 2
            )
            
            # Se a distância for pequena (polegar e indicador próximos), é joia
            # Threshold ajustável (0.05 é uma boa distância para gesto joia)
            return distancia < 0.05
        except:
            return False
    
    def detectar_gesto(self, landmarks) -> Tuple[Tuple[int, ...], List[int]]:
        """
        Detecta o gesto baseado nos landmarks da mão.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            Tupla contendo:
            - Chave do gesto (tupla ordenada de dedos estendidos)
            - Lista de dedos estendidos (não ordenada)
        """
        dedos_estendidos = self.detectar_dedos_estendidos(landmarks)
        chave = tuple(sorted(dedos_estendidos))
        return chave, dedos_estendidos
    
    def processar_frame(self, imagem_rgb):
        """
        Processa um frame de imagem para detectar mãos.
        
        Args:
            imagem_rgb: Imagem em formato RGB.
            
        Returns:
            Resultado do processamento do MediaPipe.
        """
        return self.hands.process(imagem_rgb)
    
    def liberar(self):
        """Libera recursos do detector."""
        self.hands.close()

