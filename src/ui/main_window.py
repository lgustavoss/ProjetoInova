"""
Janela principal da aplicação.
"""

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Callable
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
        self.callback_salvar: Optional[Callable] = None
        
        self._configurar_janela()
        self._criar_widgets()
        self._atualizar_lista()
    
    def _configurar_janela(self):
        """Configura propriedades da janela."""
        self.root.title(Config.WINDOW_TITLE)
        self.root.geometry(Config.WINDOW_SIZE)
    
    def _criar_widgets(self):
        """Cria os widgets da interface."""
        # Label do gesto atual
        self.label_gesto = tk.Label(
            self.root,
            text="Gesto atual: ",
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_LARGE)
        )
        self.label_gesto.pack(pady=10)
        
        # Campo de entrada de mensagem
        self.entrada_mensagem = tk.Entry(
            self.root,
            font=(Config.FONT_FAMILY, Config.FONT_SIZE_NORMAL),
            width=40
        )
        self.entrada_mensagem.pack(pady=5)
        
        # Botão salvar
        self.btn_salvar = tk.Button(
            self.root,
            text="Salvar Gesto",
            command=self._on_salvar_gesto
        )
        self.btn_salvar.pack(pady=5)
        
        # Botão voz
        self.btn_voz = tk.Button(
            self.root,
            text="Falar Mensagem",
            command=self._on_ouvir_mensagem
        )
        self.btn_voz.pack(pady=5)
        
        # Botão exportar
        self.btn_exportar = tk.Button(
            self.root,
            text="Exportar Gestos",
            command=self._on_exportar_gestos
        )
        self.btn_exportar.pack(pady=5)
        
        # Lista de gestos
        self.lista_gestos = ttk.Treeview(
            self.root,
            columns=("dedos", "mensagem"),
            show="headings"
        )
        self.lista_gestos.heading("dedos", text="Dedos")
        self.lista_gestos.heading("mensagem", text="Mensagem")
        self.lista_gestos.pack(pady=10, fill="both", expand=True)
    
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
    
    def atualizar_gesto_atual(self, chave: tuple, mensagem: str):
        """
        Atualiza o gesto atual exibido na interface.
        
        Args:
            chave: Chave do gesto detectado.
            mensagem: Mensagem associada ao gesto.
        """
        self.gesto_atual = chave
        self.label_gesto.config(text=f"Gesto atual: {mensagem}")
    
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

