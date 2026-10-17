# Az — Assistente Pessoal 100% Local 🤖

Um "Jarvis caseiro" em Python que roda **inteiro no seu PC, de graça**: conversa
por texto (ou voz), abre programas e sites, busca na web, lembra fatos sobre
você entre sessões e responde em streaming. Sem API paga, sem mandar dados pra
fora.

## Arquitetura

```
main.py         → loop principal da conversa (streaming + ciclo de ferramentas)
config.py       → modelo, personalidade (prompt de sistema), limites
ferramentas.py  → as "mãos" do Az: abrir apps, sites, arquivos, busca web, memória
memoria.py      → memória persistente (fatos + histórico) em dados/memoria.json
voz.py          → módulo opcional de voz (microfone + fala)
versao_claude/  → backup da versão que usava a API do Claude
```

O cérebro é o **Qwen 2.5 7B** rodando localmente via [Ollama](https://ollama.com).
O ciclo de ferramentas (tool use) funciona assim: o modelo decide chamar uma
função Python → o código executa → o resultado volta pro modelo → ele responde.
A busca na web usa o DuckDuckGo (gratuito, sem chave).

## Como rodar

Tudo já está instalado neste PC. Basta:

```
python main.py
```

> O Ollama precisa estar aberto (ele inicia junto com o Windows por padrão).
> A primeira resposta demora mais — é o modelo carregando na RAM.

### Instalando do zero em outra máquina

1. Instale o Ollama: https://ollama.com/download
2. Baixe o modelo: `ollama pull qwen2.5:7b`
3. Instale as dependências: `pip install -r requirements.txt`
4. Rode: `python main.py`

## Modo voz (opcional)

```
pip install SpeechRecognition pyaudio edge-tts pygame pyttsx3
python main.py --voz
```

O Az fica em espera (💤) até você dizer **"Ei Az"**:

- **"Ei Az, que horas são?"** → responde direto
- **"Ei Az"** → bipe de confirmação, aí você fala o pedido
- **"Ei Az, sair"** → encerra

O reconhecimento usa o serviço gratuito do Google (precisa de internet). A fala
usa a voz neural do Antônio (edge-tts, gratuita); sem internet, cai
automaticamente na voz offline do Windows.

## Exemplos de coisas pra pedir

- "que horas são?"
- "abre a calculadora" / "abre o youtube.com"
- "o que tem na minha pasta Downloads?"
- "lembre que eu prefiro respostas curtas"
- "qual a previsão do tempo pra amanhã em São Paulo?" (busca web)
- Em outra sessão: "o que você sabe sobre mim?"

## Dicas de desempenho

- O modelo roda na CPU — respostas saem em velocidade de leitura, não instantâneas.
- Se estiver lento demais, troque em `config.py` para `qwen2.5:3b`
  (baixe antes com `ollama pull qwen2.5:3b`) — mais rápido, um pouco menos esperto.
- Feche programas pesados: o modelo usa ~5-6 GB de RAM enquanto responde.

## Próximos passos (nível 2 → Jarvis de verdade)

- **Mais ferramentas**: e-mail, agenda, controle de casa inteligente (basta
  escrever novas funções em `ferramentas.py` e adicioná-las à lista `TODAS`)
- **Memória melhor**: busca semântica (embeddings/RAG) em vez de JSON
- **Proatividade**: tarefas agendadas que rodam o Az sozinho e te avisam
- **Voz melhor**: wake word ("Ei Az"), Whisper local, TTS neural
- **Modo híbrido**: usar o modelo local no dia a dia e chavear pra uma API
  (Claude) só em tarefas difíceis — a versão da API está em `versao_claude/`
