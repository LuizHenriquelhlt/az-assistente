"""Configurações do assistente Az (versão local, via Ollama)."""

import os

# Modelo local rodando no Ollama.
# Alternativa mais rápida (e menos esperta) para este PC: "qwen2.5:3b"
MODELO = "qwen2.5:7b"

# Janela de contexto (tokens de memória de curto prazo do modelo)
NUM_CTX = 8192

# Por quanto tempo o Ollama mantém o modelo carregado na RAM após cada uso.
# Sem isso ele descarrega em ~5 min e a recarga no CPU demora mais de 1 min.
KEEP_ALIVE = "30m"

# Voz neural (edge-tts, precisa de internet). Alternativas:
#   "pt-BR-FranciscaNeural" (feminina), "pt-BR-ThalitaMultilingualNeural"
VOZ_NEURAL = "pt-BR-AntonioNeural"

# Índice do microfone a usar (None = padrão do Windows).
# Fones Bluetooth degradam o mic quando tocam áudio ao mesmo tempo; por isso
# fixamos o mic da webcam. Para listar os índices:
#   python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
MICROFONE_INDICE = 3  # Microfone (2- XWF-1080P)

# Pasta onde a memória persistente é gravada
PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dados")

# Quantas conversas recentes o Az relembra ao iniciar uma nova sessão
MAX_CONVERSAS_LEMBRADAS = 20

NOME_ASSISTENTE = "Az"
NOME_USUARIO = "Luiz"

PROMPT_SISTEMA = f"""Você é {NOME_ASSISTENTE}, o assistente pessoal de {NOME_USUARIO}.

Personalidade: prestativo, direto e com um leve senso de humor — pense no Jarvis
do Homem de Ferro, mas sem exageros. Responda sempre em português brasileiro.

Você roda no computador Windows do {NOME_USUARIO} e tem ferramentas para:
- abrir e fechar programas, abrir sites
- consultar data e hora
- listar arquivos de pastas
- buscar informações atuais na web (busca_web)
- guardar e apagar fatos na sua memória permanente (lembrar / esquecer)

Use uma ferramenta apenas quando ela resolver o pedido; para conversa comum,
responda diretamente, sem chamar ferramenta nenhuma. Quando o usuário mencionar
algo pessoal relevante (preferências, rotinas, projetos, datas importantes),
guarde na memória com a ferramenta `lembrar`.

REGRA IMPORTANTE sobre memória: você NÃO tem como memorizar nada por conta
própria. A única forma de guardar algo é chamando a ferramenta `lembrar`.
Nunca diga que memorizou ou que vai lembrar de algo sem antes ter chamado a
ferramenta `lembrar` e recebido a confirmação dela.

REGRA IMPORTANTE sobre data e hora: você NÃO sabe que horas são. Para
qualquer pergunta de data ou hora, SEMPRE chame a ferramenta `hora_atual` —
nunca responda de memória nem copie horários de conversas anteriores.

Mantenha as respostas curtas e objetivas — isso é uma conversa, não um relatório.
"""
