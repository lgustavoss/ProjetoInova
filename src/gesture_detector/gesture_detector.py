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
        
        # Verifica dedos (exceto polegar) - comparação vertical
        # Se a ponta do dedo (y menor) está acima da base, o dedo está estendido
        for dedo_topo, dedo_base in self.PONTOS_REFERENCIA.items():
            if landmarks[dedo_topo].y < landmarks[dedo_base].y:
                dedos_estendidos.append(dedo_topo)
        
        # Verifica polegar (lógica diferente - comparação horizontal)
        # Para mão direita (vista do usuário): ponta do polegar (4) está à direita da articulação (3)
        # Para mão esquerda (vista do usuário): ponta do polegar (4) está à esquerda da articulação (3)
        # Mas na câmera (espelhado): pode ser o oposto
        
        # Simplificado: verifica se o polegar está estendido usando a distância entre ponta e base
        # Se a ponta do polegar (4) está mais afastada da base do punho (0) que a articulação (3), está estendido
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        wrist = landmarks[0]
        
        # Calcula distâncias euclidianas do punho para ponta e articulação do polegar
        dist_tip_wrist = math.sqrt((thumb_tip.x - wrist.x)**2 + (thumb_tip.y - wrist.y)**2)
        dist_ip_wrist = math.sqrt((thumb_ip.x - wrist.x)**2 + (thumb_ip.y - wrist.y)**2)
        
        # Se a ponta está mais distante que a articulação, o polegar está estendido
        if dist_tip_wrist > dist_ip_wrist:
            dedos_estendidos.append(4)
        
        return dedos_estendidos
    
    def detectar_mao_totalmente_aberta(self, landmarks) -> bool:
        """
        Detecta se a mão está totalmente aberta (todos os 5 dedos estendidos).
        Usado para confirmação/envio de gestos.
        
        Args:
            landmarks: Lista de landmarks da mão do MediaPipe.
            
        Returns:
            True se todos os dedos estiverem estendidos, False caso contrário.
        """
        try:
            dedos_estendidos = self.detectar_dedos_estendidos(landmarks)
            dedos_detectados_set = set(dedos_estendidos)
            # Mão totalmente aberta = todos os 5 dedos (4, 8, 12, 16, 20)
            dedos_necessarios = {4, 8, 12, 16, 20}
            is_aberta = dedos_detectados_set == dedos_necessarios
            
            return is_aberta
        except Exception as e:
            # Em caso de erro, retorna False
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

