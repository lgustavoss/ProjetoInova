import cv2
import mediapipe as mp
import csv
import os
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
import threading
import speech_recognition as sr
from playsound import playsound

# Inicialização do MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands()
cap = cv2.VideoCapture(0)

# Carrega gestos do CSV
gestos_csv = {}
csv_path = 'dados.csv'
if not os.path.exists(csv_path):
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('dedos,mensagem\n')

with open(csv_path, encoding='utf-8') as f:
    leitor = csv.DictReader(f)
    for linha in leitor:
        dedos = tuple(sorted(int(d) for d in linha['dedos'].split('|') if d))
        gestos_csv[dedos] = linha['mensagem']

# Função para detectar gesto
def detectar_gesto(landmarks):
    dedos_estendidos = []
    for i in [8, 12, 16, 20]:
        if landmarks[i].y < landmarks[i - 2].y:
            dedos_estendidos.append(i)
    if landmarks[4].x < landmarks[3].x:
        dedos_estendidos.append(4)
    chave = tuple(sorted(dedos_estendidos))
    mensagem = gestos_csv.get(chave, f"Gesto não reconhecido: {chave}")

    # Alerta sonoro para gestos críticos
    if "emergência" in mensagem.lower() or "pânico" in mensagem.lower():
        threading.Thread(target=lambda: playsound("alerta.mp3"), daemon=True).start()

    return chave, mensagem

# Função para salvar gesto
def salvar_gesto(chave, mensagem):
    with open(csv_path, 'a', encoding='utf-8') as f:
        linha = '|'.join(str(d) for d in chave)
        f.write(f'"{linha}","{mensagem}"\n')
    gestos_csv[chave] = mensagem
    atualizar_lista()
    messagebox.showinfo("Salvo", "✅ Novo gesto salvo com sucesso!")

# Função para ouvir mensagem por voz
def ouvir_mensagem():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        messagebox.showinfo("Microfone", "Fale a mensagem agora...")
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language='pt-BR')
        entrada_mensagem.delete(0, tk.END)       
        entrada_mensagem.insert(0, texto)
    except sr.UnknownValueError:
        messagebox.showerror("Erro", "Não entendi o que foi dito.")

# Exportar gestos para arquivo .txt
def exportar_gestos():
    with open("gestos_exportados.txt", "w", encoding="utf-8") as f:
        for dedos, mensagem in gestos_csv.items():
            f.write(f"{'|'.join(map(str, dedos))}: {mensagem}\n")
    messagebox.showinfo("Exportado", "Gestos salvos em gestos_exportados.txt")

# Atualiza lista de gestos salvos
def atualizar_lista():
    lista_gestos.delete(*lista_gestos.get_children())
    for dedos, mensagem in gestos_csv.items():
        lista_gestos.insert('', 'end', values=('|'.join(map(str, dedos)), mensagem))

# Interface gráfica
root = tk.Tk()
root.title("Reconhecimento de Gestos")
root.geometry("600x500")

label_gesto = tk.Label(root, text="Gesto atual: ", font=("Arial", 14))
label_gesto.pack(pady=10)

entrada_mensagem = tk.Entry(root, font=("Arial", 12), width=40)
entrada_mensagem.pack(pady=5)

btn_salvar = tk.Button(root, text="Salvar Gesto", command=lambda: salvar_gesto(gesto_atual, entrada_mensagem.get()))
btn_salvar.pack(pady=5)

btn_voz = tk.Button(root, text="Falar Mensagem", command=ouvir_mensagem)
btn_voz.pack(pady=5)

btn_exportar = tk.Button(root, text="Exportar Gestos", command=exportar_gestos)
btn_exportar.pack(pady=5)

lista_gestos = ttk.Treeview(root, columns=("dedos", "mensagem"), show="headings")
lista_gestos.heading("dedos", text="Dedos")
lista_gestos.heading("mensagem", text="Mensagem")
lista_gestos.pack(pady=10, fill="both", expand=True)

atualizar_lista()

# Thread para vídeo
gesto_atual = ()
def video_loop():
    global gesto_atual
    while True:
        success, img = cap.read()
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result = hands.process(img_rgb)

        if result.multi_hand_landmarks:
            for idx, handLms in enumerate(result.multi_hand_landmarks):
                mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
                chave, gesto = detectar_gesto(handLms.landmark)
                gesto_atual = chave
                cv2.putText(img, f"Mão {idx+1}: {gesto}", (10, 70 + idx*30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
                label_gesto.config(text=f"Gesto atual: {gesto}")

        cv2.imshow("Detecção de Gestos", img)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cap.release()
    cv2.destroyAllWindows()
    root.quit()

threading.Thread(target=video_loop, daemon=True).start()
root.mainloop()

