"""
Janela principal da aplicação.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Callable, Tuple
import cv2
import numpy as np
from PIL import Image, ImageTk
from src.config.config import Config
from src.data.gesto_repository import GestoRepository
from src.audio.audio_handler import AudioHandler


class MainWindow:
    """Janela principal da aplicação de reconhecimento de gestos."""
    
    def __init__(self):
        """Inicializa a janela principal."""
        self.root = tk.Tk()
        self.repositorio = GestoRepository()
        self.audio_handler = AudioHandler()
        self.gesto_atual = ()
        self.gesto_pendente: Optional[Tuple[tuple, str]] = None  # (chave, mensagem) aguardando confirmação
        self.callback_salvar: Optional[Callable] = None
        self.callback_enviar_gesto: Optional[Callable] = None  # Callback para enviar gesto via WebSocket
        
        self._configurar_janela()
        self._criar_widgets()
        self._atualizar_lista()
        self._atualizar_painel_gestos()
    
    def _configurar_janela(self):
        """Configura propriedades da janela."""
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(Config.WINDOW_SIZE)
        self.root.configure(bg='#f0f0f0')
    
    def _criar_widgets(self):
        """Cria os widgets da interface."""
        # Container principal com duas colunas
        main_container = tk.Frame(self.root, bg='#f0f0f0')
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Coluna esquerda: Vídeo e confirmação
        left_frame = tk.Frame(main_container, bg='#f0f0f0')
        left_frame.pack(side="left", fill="both", expand=True, padx=5)
        
        # Título do vídeo
        tk.Label(
            left_frame,
            text="📹 Visualização da Câmera",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold"),
            bg='#f0f0f0'
        ).pack(pady=5)
        
        # Canvas para vídeo
        self.canvas_video = tk.Canvas(
            left_frame,
            width=Config.VIDEO_WIDTH,
            height=Config.VIDEO_HEIGHT,
            bg='black',
            highlightthickness=2,
            highlightbackground='#333'
        )
        self.canvas_video.pack(pady=10)
        
        # Painel de confirmação de gesto
        self.frame_confirmacao = tk.Frame(left_frame, bg='#e8f5e9', relief=tk.RAISED, bd=2)
        self.frame_confirmacao.pack(fill="x", pady=10, padx=5)
        
        self.label_gesto_detectado = tk.Label(
            self.frame_confirmacao,
            text="Aguardando gesto...",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            bg='#e8f5e9',
            wraplength=600
        )
        self.label_gesto_detectado.pack(pady=10)
        
        self.frame_botoes_confirmacao = tk.Frame(self.frame_confirmacao, bg='#e8f5e9')
        self.frame_botoes_confirmacao.pack(pady=5)
        
        self.btn_enviar = tk.Button(
            self.frame_botoes_confirmacao,
            text="✅ Enviar para Enfermeiros",
            command=self._on_enviar_gesto,
            bg='#4caf50',
            fg='white',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL, "bold"),
            state=tk.DISABLED,
            padx=20,
            pady=10
        )
        self.btn_enviar.pack(side="left", padx=5)
        
        self.btn_cancelar = tk.Button(
            self.frame_botoes_confirmacao,
            text="❌ Cancelar",
            command=self._on_cancelar_gesto,
            bg='#f44336',
            fg='white',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            state=tk.DISABLED,
            padx=20,
            pady=10
        )
        self.btn_cancelar.pack(side="left", padx=5)
        
        # Coluna direita: Gestos disponíveis e configurações
        right_frame = tk.Frame(main_container, bg='#f0f0f0')
        right_frame.pack(side="right", fill="both", expand=False, padx=5)
        
        # Título dos gestos disponíveis
        tk.Label(
            right_frame,
            text="📋 Gestos Disponíveis",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold"),
            bg='#f0f0f0'
        ).pack(pady=5)
        
        # Frame scrollável para gestos
        frame_scroll = tk.Frame(right_frame, bg='#f0f0f0')
        frame_scroll.pack(fill="both", expand=True)
        
        scrollbar_gestos = tk.Scrollbar(frame_scroll)
        scrollbar_gestos.pack(side="right", fill="y")
        
        self.canvas_gestos = tk.Canvas(
            frame_scroll,
            width=300,
            height=400,
            bg='white',
            yscrollcommand=scrollbar_gestos.set
        )
        self.canvas_gestos.pack(side="left", fill="both", expand=True)
        scrollbar_gestos.config(command=self.canvas_gestos.yview)
        
        self.frame_gestos_cards = tk.Frame(self.canvas_gestos, bg='white')
        self.canvas_gestos.create_window((0, 0), window=self.frame_gestos_cards, anchor="nw")
        
        # Frame de configuração (parte inferior direita)
        frame_config = tk.LabelFrame(
            right_frame,
            text="⚙️ Configurações",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            bg='#f0f0f0'
        )
        frame_config.pack(fill="x", pady=10)
        
        # Campo de entrada de mensagem
        tk.Label(
            frame_config,
            text="Mensagem:",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            bg='#f0f0f0'
        ).pack(anchor="w", padx=5, pady=2)
        
        self.entrada_mensagem = tk.Entry(
            frame_config,
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            width=30
        )
        self.entrada_mensagem.pack(padx=5, pady=5, fill="x")
        
        # Botões de ação
        btn_frame = tk.Frame(frame_config, bg='#f0f0f0')
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        self.btn_salvar = tk.Button(
            btn_frame,
            text="💾 Salvar Gesto",
            command=self._on_salvar_gesto,
            bg='#2196f3',
            fg='white',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
        )
        self.btn_salvar.pack(fill="x", pady=2)
        
        self.btn_voz = tk.Button(
            btn_frame,
            text="🎤 Falar Mensagem",
            command=self._on_ouvir_mensagem,
            bg='#ff9800',
            fg='white',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
        )
        self.btn_voz.pack(fill="x", pady=2)
        
        self.btn_exportar = tk.Button(
            btn_frame,
            text="📤 Exportar Gestos",
            command=self._on_exportar_gestos,
            bg='#9c27b0',
            fg='white',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
        )
        self.btn_exportar.pack(fill="x", pady=2)
        
        # Lista de gestos (oculta, mantida para compatibilidade)
        self.lista_gestos = ttk.Treeview(
            right_frame,
            columns=("dedos", "mensagem"),
            show="headings",
            height=0  # Oculto
        )
    
    def _on_salvar_gesto(self):
        """Callback para salvar gesto."""
        mensagem = self.entrada_mensagem.get().strip()
        
        if not mensagem:
            messagebox.showwarning("Aviso", "Por favor, digite uma mensagem.")
            return
        
        if not self.gesto_atual:
            messagebox.showwarning("Aviso", "Nenhum gesto detectado.")
            return
        
        if self.repositorio.salvar_gesto(self.gesto_atual, mensagem):
            self._atualizar_lista()
            self._atualizar_painel_gestos()
            messagebox.showinfo("Salvo", "✅ Novo gesto salvo com sucesso!")
            self.entrada_mensagem.delete(0, tk.END)
        else:
            messagebox.showerror("Erro", "Não foi possível salvar o gesto.")
    
    def _on_ouvir_mensagem(self):
        """Callback para reconhecimento de voz."""
        messagebox.showinfo("Microfone", "Fale a mensagem agora...")
        texto = self.audio_handler.reconhecer_voz()
        
        if texto:
            self.entrada_mensagem.delete(0, tk.END)
            self.entrada_mensagem.insert(0, texto)
        else:
            messagebox.showerror("Erro", "Não entendi o que foi dito.")
    
    def _on_exportar_gestos(self):
        """Callback para exportar gestos."""
        if self.repositorio.exportar_para_txt():
            messagebox.showinfo(
                "Exportado",
                f"Gestos salvos em {Config.EXPORT_PATH}"
            )
        else:
            messagebox.showerror("Erro", "Não foi possível exportar os gestos.")
    
    def _atualizar_lista(self):
        """Atualiza a lista de gestos salvos."""
        self.lista_gestos.delete(*self.lista_gestos.get_children())
        
        for dedos, mensagem in self.repositorio.obter_todos_gestos().items():
            linha_dedos = '|'.join(map(str, dedos))
            self.lista_gestos.insert('', 'end', values=(linha_dedos, mensagem))
        
        # Atualiza também o painel visual
        self._atualizar_painel_gestos()
    
    def atualizar_frame_video(self, frame_bgr):
        """
        Atualiza o frame de vídeo no canvas.
        
        Args:
            frame_bgr: Frame BGR do OpenCV.
        """
        try:
            # Redimensiona frame se necessário
            height, width = frame_bgr.shape[:2]
            if width != Config.VIDEO_WIDTH or height != Config.VIDEO_HEIGHT:
                frame_bgr = cv2.resize(frame_bgr, (Config.VIDEO_WIDTH, Config.VIDEO_HEIGHT))
            
            # Converte BGR para RGB
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # Converte para PIL Image
            image = Image.fromarray(frame_rgb)
            photo = ImageTk.PhotoImage(image=image)
            
            # Atualiza canvas
            self.canvas_video.create_image(0, 0, anchor=tk.NW, image=photo)
            self.canvas_video.image = photo  # Mantém referência
            
        except Exception as e:
            print(f"Erro ao atualizar frame de vídeo: {e}")
    
    def atualizar_gesto_atual(self, chave: tuple, mensagem: str):
        """
        Atualiza o gesto atual e pede confirmação antes de enviar.
        
        Args:
            chave: Chave do gesto detectado.
            mensagem: Mensagem associada ao gesto.
        """
        self.gesto_atual = chave
        
        # Se gesto foi reconhecido (tem mensagem), pede confirmação
        if mensagem and not mensagem.startswith("Gesto não reconhecido"):
            self.gesto_pendente = (chave, mensagem)
            
            # Verifica se é crítico
            is_critico = self.audio_handler.verificar_mensagem_critica(mensagem)
            cor_fundo = '#ffebee' if is_critico else '#e8f5e9'
            cor_texto = '#c62828' if is_critico else '#2e7d32'
            emoji = '🔴' if is_critico else '✅'
            
            self.frame_confirmacao.config(bg=cor_fundo)
            self.label_gesto_detectado.config(
                text=f"{emoji} Gesto Detectado!\n\n{mensagem}\n\nDeseja enviar para os enfermeiros?",
                bg=cor_fundo,
                fg=cor_texto,
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE, "bold")
            )
            
            # Habilita botões
            self.btn_enviar.config(state=tk.NORMAL)
            self.btn_cancelar.config(state=tk.NORMAL)
            
            # Reproduz alerta se crítico
            if is_critico:
                self.audio_handler.reproduzir_alerta()
        else:
            # Gesto não reconhecido
            self.gesto_pendente = None
            self.frame_confirmacao.config(bg='#fff3e0')
            self.label_gesto_detectado.config(
                text=f"⚠️ {mensagem}\n\nTente fazer o gesto novamente.",
                bg='#fff3e0',
                fg='#e65100',
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
            )
            self.btn_enviar.config(state=tk.DISABLED)
            self.btn_cancelar.config(state=tk.DISABLED)
        
        # Atualiza destaque no painel de gestos
        self._destacar_gesto(chave)
    
    def _destacar_gesto(self, chave: tuple):
        """Destaca o gesto detectado no painel de gestos."""
        # Remove destaque anterior
        for widget in self.frame_gestos_cards.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.config(bg='white', relief=tk.FLAT)
        
        # Destaca gesto atual se existir
        if chave in self.repositorio.obter_todos_gestos():
            # Encontra o card correspondente e destaca
            for idx, widget in enumerate(self.frame_gestos_cards.winfo_children()):
                if isinstance(widget, tk.Frame) and hasattr(widget, 'gesto_chave'):
                    if widget.gesto_chave == chave:
                        widget.config(bg='#e3f2fd', relief=tk.RAISED, bd=3)
                        break
    
    def _on_enviar_gesto(self):
        """Callback para enviar gesto confirmado."""
        if self.gesto_pendente and self.callback_enviar_gesto:
            chave, mensagem = self.gesto_pendente
            self.callback_enviar_gesto(chave, mensagem)
            
            # Feedback visual
            self.frame_confirmacao.config(bg='#c8e6c9')
            self.label_gesto_detectado.config(
                text=f"✅ Mensagem enviada!\n\n{mensagem}\n\nOs enfermeiros foram notificados.",
                bg='#c8e6c9',
                fg='#1b5e20',
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
            )
            
            # Desabilita botões temporariamente
            self.btn_enviar.config(state=tk.DISABLED)
            self.btn_cancelar.config(state=tk.DISABLED)
            
            # Limpa após 3 segundos
            self.root.after(3000, self._limpar_confirmacao)
    
    def _on_cancelar_gesto(self):
        """Callback para cancelar envio de gesto."""
        self.gesto_pendente = None
        self._limpar_confirmacao()
    
    def _limpar_confirmacao(self):
        """Limpa o painel de confirmação."""
        self.gesto_pendente = None
        self.frame_confirmacao.config(bg='#e8f5e9')
        self.label_gesto_detectado.config(
            text="Aguardando gesto...",
            bg='#e8f5e9',
            fg='black',
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL)
        )
        self.btn_enviar.config(state=tk.DISABLED)
        self.btn_cancelar.config(state=tk.DISABLED)
    
    def _atualizar_painel_gestos(self):
        """Atualiza o painel visual de gestos disponíveis."""
        # Limpa cards existentes
        for widget in self.frame_gestos_cards.winfo_children():
            widget.destroy()
        
        gestos = self.repositorio.obter_todos_gestos()
        
        if not gestos:
            tk.Label(
                self.frame_gestos_cards,
                text="Nenhum gesto salvo.\nSalve gestos para aparecerem aqui.",
                font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
                bg='white',
                fg='gray',
                justify=tk.CENTER
            ).pack(pady=20)
        else:
            for chave, mensagem in gestos.items():
                card = tk.Frame(
                    self.frame_gestos_cards,
                    bg='white',
                    relief=tk.RAISED,
                    bd=2,
                    padx=10,
                    pady=10
                )
                card.pack(fill="x", padx=5, pady=5)
                card.gesto_chave = chave  # Armazena chave para destacar depois
                
                # Ícone dos dedos
                dedos_str = '|'.join(map(str, chave))
                tk.Label(
                    card,
                    text=f"👋 {dedos_str}",
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL, "bold"),
                    bg='white'
                ).pack(anchor="w")
                
                # Mensagem
                tk.Label(
                    card,
                    text=mensagem,
                    font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
                    bg='white',
                    wraplength=280,
                    justify=tk.LEFT
                ).pack(anchor="w", pady=2)
        
        # Atualiza scroll
        self.frame_gestos_cards.update_idletasks()
        self.canvas_gestos.config(scrollregion=self.canvas_gestos.bbox("all"))
    
    def verificar_e_reproduzir_alerta(self, mensagem: str):
        """
        Verifica se a mensagem é crítica e reproduz alerta se necessário.
        
        Args:
            mensagem: Mensagem a verificar.
        """
        if self.audio_handler.verificar_mensagem_critica(mensagem):
            self.audio_handler.reproduzir_alerta()
    
    def executar(self):
        """Inicia o loop principal da interface."""
        self.root.mainloop()
    
    def fechar(self):
        """Fecha a janela."""
        self.root.quit()
        self.root.destroy()

