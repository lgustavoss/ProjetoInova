"""
Repositório para gerenciamento de gestos.
"""

import csv
from typing import Dict, Tuple, Optional
from pathlib import Path
from src.config.config import Config


class GestoRepository:
    """Gerencia o armazenamento e recuperação de gestos."""
    
    def __init__(self, csv_path: Optional[Path] = None):
        """
        Inicializa o repositório de gestos.
        
        Args:
            csv_path: Caminho para o arquivo CSV. Se None, usa o padrão da Config.
        """
        self.csv_path = csv_path or Config.CSV_PATH
        Config.ensure_data_file_exists()
        self._gestos: Dict[Tuple[int, ...], str] = {}
        self._carregar_gestos()
    
    def _carregar_gestos(self):
        """Carrega gestos do arquivo CSV."""
        self._gestos.clear()
        
        if not self.csv_path.exists():
            return
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                leitor = csv.DictReader(f)
                for linha in leitor:
                    dedos_str = linha.get('dedos', '').strip()
                    mensagem = linha.get('mensagem', '').strip()
                    
                    if not dedos_str:
                        continue
                    
                    try:
                        # Remove aspas extras e espaços
                        dedos_str = dedos_str.strip('"').strip()
                        if not dedos_str:
                            # Ignora gestos vazios (mão fechada deve ser usada apenas para cancelamento)
                            continue
                        
                        # Converte para tupla de inteiros, filtrando valores inválidos
                        dedos_lista = []
                        for d in dedos_str.split('|'):
                            d = d.strip()
                            if d:
                                try:
                                    dedo = int(d)
                                    # Índices válidos dos dedos no MediaPipe: 4, 8, 12, 16, 20
                                    if dedo in [4, 8, 12, 16, 20]:
                                        dedos_lista.append(dedo)
                                    # Ignora índices inválidos (como 0)
                                except ValueError:
                                    continue
                        
                        # Só adiciona se tiver pelo menos um dedo válido
                        if len(dedos_lista) > 0:
                            dedos = tuple(sorted(set(dedos_lista)))  # Remove duplicatas e ordena
                            
                            # CRÍTICO: Ignora mão totalmente aberta (4, 8, 12, 16, 20) do CSV
                            # Mão totalmente aberta deve ser usada APENAS para confirmação/envio, não como gesto válido
                            if dedos == (4, 8, 12, 16, 20):
                                continue  # Pula este gesto, não adiciona ao repositório
                            
                            # Se já existir, mantém a primeira ocorrência (ou pode sobrescrever com a última)
                            if dedos not in self._gestos:
                                self._gestos[dedos] = mensagem
                            # Se já existir e mensagem for diferente, usa a mais recente
                            else:
                                self._gestos[dedos] = mensagem
                    except ValueError:
                        continue
        except Exception as e:
            print(f"Erro ao carregar gestos: {e}")
    
    def obter_mensagem(self, chave: Tuple[int, ...]) -> Optional[str]:
        """
        Obtém a mensagem associada a uma chave de gesto.
        
        Args:
            chave: Tupla de dedos estendidos.
            
        Returns:
            Mensagem associada ou None se não encontrada.
        """
        # CRÍTICO: Nunca retorna mensagem para gesto vazio (mão fechada)
        # Mão fechada deve ser usada APENAS para cancelamento
        if not chave or len(chave) == 0:
            return None
        
        # CRÍTICO: Nunca retorna mensagem para mão totalmente aberta (todos os 5 dedos)
        # Mão totalmente aberta (4, 8, 12, 16, 20) deve ser usada APENAS para confirmação/envio
        if chave == (4, 8, 12, 16, 20):
            return None
        
        # Valida que todos os índices são válidos (4, 8, 12, 16, 20)
        indices_validos = {4, 8, 12, 16, 20}
        if not all(d in indices_validos for d in chave):
            return None
        
        return self._gestos.get(chave)
    
    def salvar_gesto(self, chave: Tuple[int, ...], mensagem: str) -> bool:
        """
        Salva um novo gesto no arquivo CSV.
        
        Args:
            chave: Tupla de dedos estendidos.
            mensagem: Mensagem associada ao gesto.
            
        Returns:
            True se salvo com sucesso, False caso contrário.
        """
        try:
            with open(self.csv_path, 'a', encoding='utf-8', newline='') as f:
                linha = '|'.join(str(d) for d in chave)
                f.write(f'"{linha}","{mensagem}"\n')
            
            self._gestos[chave] = mensagem
            return True
        except Exception as e:
            print(f"Erro ao salvar gesto: {e}")
            return False
    
    def obter_todos_gestos(self) -> Dict[Tuple[int, ...], str]:
        """
        Retorna todos os gestos salvos.
        
        Returns:
            Dicionário com todos os gestos.
        """
        return self._gestos.copy()
    
    def exportar_para_txt(self, caminho_arquivo: Optional[Path] = None) -> bool:
        """
        Exporta todos os gestos para um arquivo de texto.
        
        Args:
            caminho_arquivo: Caminho do arquivo de exportação. Se None, usa o padrão.
            
        Returns:
            True se exportado com sucesso, False caso contrário.
        """
        caminho = caminho_arquivo or Config.EXPORT_PATH
        
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                for dedos, mensagem in self._gestos.items():
                    linha_dedos = '|'.join(map(str, dedos))
                    f.write(f"{linha_dedos}: {mensagem}\n")
            return True
        except Exception as e:
            print(f"Erro ao exportar gestos: {e}")
            return False
    
    def recarregar(self):
        """Recarrega os gestos do arquivo CSV."""
        self._carregar_gestos()

