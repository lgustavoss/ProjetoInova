# ProjetoInova - Sistema de Reconhecimento de Gestos

Sistema de reconhecimento de gestos de mão usando MediaPipe, OpenCV e interface gráfica Tkinter.

## 📁 Estrutura do Projeto

```
ProjetoInova/
├── src/                          # Código fonte principal
│   ├── __init__.py              # Inicialização do pacote
│   ├── config/                  # Módulo de configuração
│   │   ├── __init__.py
│   │   └── config.py           # Configurações da aplicação
│   ├── data/                    # Módulo de gerenciamento de dados
│   │   ├── __init__.py
│   │   └── gesto_repository.py  # Repositório de gestos (CSV)
│   ├── gesture_detector/        # Módulo de detecção de gestos
│   │   ├── __init__.py
│   │   └── gesture_detector.py  # Detector usando MediaPipe
│   ├── audio/                   # Módulo de áudio
│   │   ├── __init__.py
│   │   └── audio_handler.py     # Reconhecimento de voz e alertas
│   ├── video/                   # Módulo de processamento de vídeo
│   │   ├── __init__.py
│   │   └── video_processor.py   # Processador de vídeo da câmera
│   └── ui/                      # Módulo de interface gráfica
│       ├── __init__.py
│       └── main_window.py       # Janela principal Tkinter
├── main.py                      # Ponto de entrada da aplicação
├── requirements.txt             # Dependências do projeto
├── dados.csv                    # Banco de dados de gestos
└── README.md                    # Este arquivo
```

## 🏗️ Arquitetura

A aplicação foi organizada seguindo o princípio de **Separação de Responsabilidades**:

- **`config/`**: Centraliza todas as configurações da aplicação
- **`data/`**: Gerencia persistência de dados (leitura/escrita de CSV)
- **`gesture_detector/`**: Lógica de detecção de gestos usando MediaPipe
- **`audio/`**: Funcionalidades de áudio (reconhecimento de voz, alertas)
- **`video/`**: Processamento de vídeo da câmera
- **`ui/`**: Interface gráfica (Tkinter)

## 🚀 Como Executar

1. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

2. **Execute a aplicação:**
```bash
python main.py
```

## 📦 Dependências

- `opencv-python>=4.8.0` - Processamento de vídeo
- `mediapipe>=0.10.0` - Detecção de gestos
- `SpeechRecognition>=3.10.0` - Reconhecimento de voz
- `playsound>=1.3.0` - Reprodução de áudio

## 🎯 Funcionalidades

- ✅ Detecção de gestos de mão em tempo real
- ✅ Salvamento de gestos personalizados
- ✅ Reconhecimento de voz para mensagens
- ✅ Alertas sonoros para gestos críticos
- ✅ Exportação de gestos para arquivo texto
- ✅ Interface gráfica intuitiva

## 🔧 Boas Práticas Implementadas

1. **Separação de Responsabilidades**: Cada módulo tem uma responsabilidade única
2. **Configuração Centralizada**: Todas as configurações em um único lugar
3. **Tratamento de Erros**: Try/except em operações críticas
4. **Type Hints**: Tipagem para melhor legibilidade e manutenção
5. **Docstrings**: Documentação em todos os módulos e classes
6. **Código Limpo**: Nomes descritivos e estrutura organizada
7. **Threading**: Processamento de vídeo em thread separada
8. **Callbacks**: Comunicação entre módulos via callbacks

## 📝 Notas

- O arquivo `dados.csv` é criado automaticamente se não existir
- Gestos críticos (contendo palavras como "emergência", "pânico", "urgente") disparam alertas sonoros
- Pressione ESC na janela de vídeo para fechar a aplicação

