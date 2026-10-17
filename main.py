"""Az — assistente pessoal 100% local (Ollama + Qwen 2.5).

Uso:
    python main.py          # modo texto
    python main.py --voz    # modo voz (requer pacotes extras, ver voz.py)

Requer o Ollama instalado e o modelo baixado (ollama pull qwen2.5:7b).
"""

import argparse
import sys

import ollama

import ferramentas
import voz
from config import MODELO, NUM_CTX, KEEP_ALIVE, PROMPT_SISTEMA, NOME_ASSISTENTE
from memoria import Memoria

# Máximo de rodadas ferramenta -> resposta por turno (evita loop infinito)
MAX_RODADAS = 8


def montar_prompt_sistema(memoria: Memoria) -> str:
    contexto = memoria.contexto()
    if contexto:
        return PROMPT_SISTEMA + "\n\n" + contexto
    return PROMPT_SISTEMA


def executar_ferramenta(chamada) -> str:
    nome = chamada.function.name
    funcao = ferramentas.FUNCOES.get(nome)
    if funcao is None:
        return f"Ferramenta desconhecida: {nome}"
    try:
        return str(funcao(**(chamada.function.arguments or {})))
    except Exception as erro:
        return f"Erro ao executar {nome}: {erro}"


def responder(memoria: Memoria, mensagens: list) -> str:
    """Executa um turno completo: modelo responde, chama ferramentas se quiser,
    recebe os resultados e continua, até produzir a resposta final."""
    conteudo_final = ""
    for _ in range(MAX_RODADAS):
        stream = ollama.chat(
            model=MODELO,
            messages=[{"role": "system", "content": montar_prompt_sistema(memoria)}] + mensagens,
            tools=ferramentas.TODAS,
            stream=True,
            options={"num_ctx": NUM_CTX},
            keep_alive=KEEP_ALIVE,
        )

        conteudo = ""
        chamadas = []
        for pedaco in stream:
            msg = pedaco.message
            if msg.content:
                print(msg.content, end="", flush=True)
                conteudo += msg.content
            if msg.tool_calls:
                chamadas.extend(msg.tool_calls)

        mensagens.append(
            {
                "role": "assistant",
                "content": conteudo,
                "tool_calls": [c.model_dump() for c in chamadas],
            }
        )

        if not chamadas:
            conteudo_final = conteudo
            break

        for chamada in chamadas:
            print(f"\n🔧 [{chamada.function.name}]", flush=True)
            resultado = executar_ferramenta(chamada)
            mensagens.append(
                {
                    "role": "tool",
                    "content": resultado,
                    "tool_name": chamada.function.name,
                }
            )

    print()
    return conteudo_final


def main():
    parser = argparse.ArgumentParser(description=f"{NOME_ASSISTENTE} — assistente pessoal local")
    parser.add_argument("--voz", action="store_true", help="ativa entrada e saída por voz")
    args = parser.parse_args()

    modo_voz = args.voz
    if modo_voz and not voz.DISPONIVEL:
        print("⚠️ Modo voz indisponível: instale com "
              "'pip install SpeechRecognition pyttsx3 pyaudio'. Seguindo em modo texto.")
        modo_voz = False

    memoria = Memoria()
    ferramentas.memoria = memoria  # dá às ferramentas acesso à memória

    # Aquecimento: carrega o modelo na RAM já na largada (prompt vazio só
    # carrega, não gera nada), pra primeira resposta não demorar
    print("⏳ Carregando o modelo na RAM...", flush=True)
    try:
        ollama.generate(model=MODELO, prompt="",
                        options={"num_ctx": NUM_CTX}, keep_alive=KEEP_ALIVE)
    except ConnectionError:
        print("⚠️ Não consegui falar com o Ollama. Abra o aplicativo Ollama "
              "(ou rode 'ollama serve') e tente de novo.")
        sys.exit(1)

    mensagens: list = []  # histórico completo da sessão atual

    print(f"⚡ {NOME_ASSISTENTE} online (modelo local: {MODELO})."
          + (" Diga 'Az' para me chamar; 'Az, sair' para encerrar."
             if modo_voz else " Digite 'sair' para encerrar."))

    while True:
        try:
            if modo_voz:
                entrada = voz.aguardar_wake()
                if not entrada:
                    continue
            else:
                entrada = input("\nVocê: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nAté logo! 👋")
            break

        if not entrada:
            continue
        if entrada.lower() in ("sair", "tchau", "exit", "quit"):
            print(f"{NOME_ASSISTENTE}: Até logo! 👋")
            break

        mensagens.append({"role": "user", "content": entrada})
        print(f"{NOME_ASSISTENTE}: ", end="", flush=True)

        try:
            resposta = responder(memoria, mensagens)
        except ConnectionError:
            print("\n⚠️ Não consegui falar com o Ollama. Abra o aplicativo Ollama "
                  "(ou rode 'ollama serve') e tente de novo.")
            continue
        except ollama.ResponseError as erro:
            if "not found" in str(erro).lower():
                print(f"\n⚠️ Modelo '{MODELO}' não encontrado. "
                      f"Baixe com: ollama pull {MODELO}")
                sys.exit(1)
            print(f"\n⚠️ Erro do Ollama: {erro}")
            continue

        memoria.registrar_conversa(entrada, resposta)
        if modo_voz and resposta:
            voz.falar(resposta)


if __name__ == "__main__":
    main()
