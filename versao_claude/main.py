"""Az — assistente pessoal com Claude.

Uso:
    python main.py          # modo texto
    python main.py --voz    # modo voz (requer pacotes extras, ver voz.py)

Requer a variável de ambiente ANTHROPIC_API_KEY.
"""

import argparse
import sys

import anthropic

import ferramentas
import voz
from config import MODELO, MAX_TOKENS, PROMPT_SISTEMA, NOME_ASSISTENTE
from memoria import Memoria


def montar_prompt_sistema(memoria: Memoria) -> str:
    contexto = memoria.contexto()
    if contexto:
        return PROMPT_SISTEMA + "\n\n" + contexto
    return PROMPT_SISTEMA


def responder(client: anthropic.Anthropic, memoria: Memoria, mensagens: list) -> str:
    """Executa um turno completo do assistente, com streaming e ferramentas.

    O tool runner do SDK cuida do ciclo pedir-ferramenta -> executar -> devolver
    resultado. Espelhamos o histórico em `mensagens` para persistir a conversa e
    para reiniciar o runner caso uma ferramenta de servidor pause o turno
    (stop_reason == "pause_turn").
    """
    while True:
        runner = client.beta.messages.tool_runner(
            model=MODELO,
            max_tokens=MAX_TOKENS,
            system=montar_prompt_sistema(memoria),
            tools=ferramentas.TODAS,
            messages=mensagens,
            stream=True,
        )
        ultima = None
        for stream in runner:
            for evento in stream:
                if evento.type == "content_block_start":
                    tipo = evento.content_block.type
                    if tipo == "thinking":
                        print("🧠 ", end="", flush=True)
                    elif tipo == "server_tool_use":
                        print("\n🔎 [buscando na web...]", flush=True)
                    elif tipo == "tool_use":
                        print(f"\n🔧 [{evento.content_block.name}]", flush=True)
                elif (
                    evento.type == "content_block_delta"
                    and evento.delta.type == "text_delta"
                ):
                    print(evento.delta.text, end="", flush=True)

            mensagem = stream.get_final_message()
            ultima = mensagem
            mensagens.append({"role": "assistant", "content": mensagem.content})
            resultado_ferramentas = runner.generate_tool_call_response()
            if resultado_ferramentas is not None:
                mensagens.append(resultado_ferramentas)

        if ultima is None or ultima.stop_reason != "pause_turn":
            break

    print()
    if ultima is not None and ultima.stop_reason == "refusal":
        return "(o modelo recusou este pedido por política de segurança)"
    if ultima is None:
        return ""
    return "".join(b.text for b in ultima.content if b.type == "text")


def main():
    parser = argparse.ArgumentParser(description=f"{NOME_ASSISTENTE} — assistente pessoal")
    parser.add_argument("--voz", action="store_true", help="ativa entrada e saída por voz")
    args = parser.parse_args()

    modo_voz = args.voz
    if modo_voz and not voz.DISPONIVEL:
        print("⚠️ Modo voz indisponível: instale com "
              "'pip install SpeechRecognition pyttsx3 pyaudio'. Seguindo em modo texto.")
        modo_voz = False

    client = anthropic.Anthropic()
    memoria = Memoria()
    ferramentas.memoria = memoria  # dá às ferramentas acesso à memória

    mensagens: list = []  # histórico completo da sessão atual

    print(f"⚡ {NOME_ASSISTENTE} online. Digite 'sair' para encerrar."
          + (" (modo voz ativo — diga 'sair' para encerrar)" if modo_voz else ""))

    while True:
        try:
            if modo_voz:
                entrada = voz.ouvir()
                if not entrada:
                    continue
                print(f"Você: {entrada}")
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
            resposta = responder(client, memoria, mensagens)
        except anthropic.AuthenticationError:
            print("\n⚠️ API key inválida ou ausente. Defina a variável ANTHROPIC_API_KEY.")
            sys.exit(1)
        except anthropic.RateLimitError:
            print("\n⚠️ Limite de requisições atingido. Aguarde um pouco e tente de novo.")
            continue
        except anthropic.APIStatusError as erro:
            print(f"\n⚠️ Erro da API ({erro.status_code}): {erro.message}")
            continue
        except anthropic.APIConnectionError:
            print("\n⚠️ Sem conexão com a API. Verifique sua internet.")
            continue

        memoria.registrar_conversa(entrada, resposta)
        if modo_voz and resposta:
            voz.falar(resposta)


if __name__ == "__main__":
    main()
