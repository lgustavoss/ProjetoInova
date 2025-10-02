import cv2
import mediapipe as mp
import csv
import os

# Inicialização do MediaPipe
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
hands = mp_hands.Hands()
cap = cv2.VideoCapture(0)

# 🗂️ Carrega os gestos do CSV
gestos_csv = {}
csv_path = 'dados.csv'

# Cria o arquivo se não existir
if not os.path.exists(csv_path):
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write('dedos,mensagem\n')

# Lê os gestos existentes
with open(csv_path, encoding='utf-8') as f:
    leitor = csv.DictReader(f)
    for linha in leitor:
        dedos = tuple(sorted(int(d) for d in linha['dedos'].split('|')))
        gestos_csv[dedos] = linha['mensagem']

# 🧠 Função de detecção
def detectar_gesto(landmarks):
    dedos_estendidos = []
    for i in [8, 12, 16, 20]:
        if landmarks[i].y < landmarks[i - 2].y:
            dedos_estendidos.append(i)
    if landmarks[4].x < landmarks[3].x:
        dedos_estendidos.append(4)

    chave = tuple(sorted(dedos_estendidos))
    print("Dedos estendidos:", chave)
    return gestos_csv.get(chave, f"Gesto não reconhecido: {chave}")

# 📝 Função para salvar novo gesto
def salvar_gesto(chave, mensagem):
    with open(csv_path, 'a', encoding='utf-8') as f:
        linha = '|'.join(str(d) for d in chave)
        f.write(f'"{linha}","{mensagem}"\n')
    gestos_csv[chave] = mensagem
    print("✅ Novo gesto salvo com sucesso!")

# 🎥 Loop principal
ultimo_gesto = ""
while True:
    success, img = cap.read()
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    result = hands.process(img_rgb)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(img, handLms, mp_hands.HAND_CONNECTIONS)
            gesto = detectar_gesto(handLms.landmark)
            ultimo_gesto = gesto
            cv2.putText(img, gesto, (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Detecção de Gestos", img)

    tecla = cv2.waitKey(1) & 0xFF
    if tecla == 27:  # ESC
        break
    elif tecla == ord('s') and "Gesto não reconhecido" in ultimo_gesto:
        dedos = eval(ultimo_gesto.split(":")[1].strip())
        nova_mensagem = input("Digite a mensagem para esse gesto: ")
        salvar_gesto(dedos, nova_mensagem)
         # Sai do loop se apertar a tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


cap.release()
cv2.destroyAllWindows()

