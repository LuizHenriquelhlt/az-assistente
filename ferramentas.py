"""Ferramentas que o Az pode usar — as "mãos" do assistente.

Funções Python comuns: o Ollama gera o schema da ferramenta a partir da
assinatura e da docstring (estilo Google, com seção Args). Para dar novos
poderes ao Az, escreva uma função nova aqui e adicione-a à lista TODAS.
"""

import os
import subprocess
import webbrowser
from datetime import datetime

# Instância de memória compartilhada — definida pelo main.py na inicialização
memoria = None

# Programas comuns do Windows: apelido -> comando
PROGRAMAS = {
    "calculadora": "calc",
    "bloco de notas": "notepad",
    "notepad": "notepad",
    "paint": "mspaint",
    "explorador": "explorer",
    "explorer": "explorer",
    "terminal": "wt",
    "cmd": "cmd",
    "configurações": "ms-settings:",
    "spotify": "spotify",
    "chrome": "chrome",
    "edge": "msedge",
    "word": "winword",
    "excel": "excel",
    "vscode": "code",
    "code": "code",
}


def hora_atual() -> str:
    """Retorna a data e a hora atuais do computador do usuário."""
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
    agora = datetime.now()
    return f"{dias[agora.weekday()]}, {agora.strftime('%d/%m/%Y %H:%M:%S')}"


def abrir_programa(nome: str) -> str:
    """Abre um programa no computador do usuário.

    Args:
        nome: Nome do programa, ex.: "calculadora", "bloco de notas", "spotify",
            "chrome", "vscode". Também aceita o nome de um executável.
    """
    comando = PROGRAMAS.get(nome.strip().lower(), nome.strip())
    try:
        if comando.startswith("ms-settings:"):
            os.startfile(comando)
        else:
            subprocess.Popen(comando, shell=True)
        return f"Programa '{nome}' aberto."
    except Exception as erro:
        return f"Erro ao abrir '{nome}': {erro}"


# Processos correspondentes, para conseguir fechá-los
PROCESSOS = {
    "calculadora": ["CalculatorApp.exe", "Calculator.exe"],
    "bloco de notas": ["notepad.exe"],
    "notepad": ["notepad.exe"],
    "paint": ["mspaint.exe"],
    "spotify": ["Spotify.exe"],
    "chrome": ["chrome.exe"],
    "edge": ["msedge.exe"],
    "word": ["WINWORD.EXE"],
    "excel": ["EXCEL.EXE"],
    "vscode": ["Code.exe"],
    "code": ["Code.exe"],
}


def _processo_rodando(exe: str) -> bool:
    saida = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {exe}"], capture_output=True, text=True
    )
    return exe.lower() in saida.stdout.lower()


def fechar_programa(nome: str) -> str:
    """Fecha um programa que está aberto no computador do usuário.

    Args:
        nome: Nome do programa a fechar, ex.: "calculadora", "spotify", "chrome".
    """
    import time

    candidatos = PROCESSOS.get(nome.strip().lower())
    if candidatos is None:
        exe = nome.strip()
        candidatos = [exe if exe.lower().endswith(".exe") else exe + ".exe"]

    for exe in candidatos:
        if not _processo_rodando(exe):
            continue
        # 1º tenta o fechamento educado (deixa o programa salvar/encerrar bem)
        subprocess.run(["taskkill", "/IM", exe], capture_output=True, text=True)
        time.sleep(1.5)
        if not _processo_rodando(exe):
            return f"Programa '{nome}' fechado."
        # ainda aberto: força o encerramento
        subprocess.run(["taskkill", "/F", "/IM", exe], capture_output=True, text=True)
        time.sleep(0.5)
        if not _processo_rodando(exe):
            return f"Programa '{nome}' fechado (foi preciso forçar)."
        return f"Tentei fechar '{nome}', mas ele resistiu. Verifique manualmente."
    return f"Não encontrei '{nome}' aberto para fechar."


def abrir_site(url: str) -> str:
    """Abre um site no navegador padrão do usuário.

    Args:
        url: Endereço do site, ex.: "youtube.com" ou "https://github.com".
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Site {url} aberto no navegador."


def listar_arquivos(pasta: str) -> str:
    """Lista os arquivos e subpastas de uma pasta do computador.

    Args:
        pasta: Caminho da pasta, ex.: "C:/Users/Luiz/Documents" ou "Downloads"
            (nomes curtos são resolvidos dentro da pasta do usuário).
    """
    caminho = os.path.expanduser(pasta)
    if not os.path.isabs(caminho):
        caminho = os.path.join(os.path.expanduser("~"), pasta)
    if not os.path.isdir(caminho):
        return f"Pasta não encontrada: {caminho}"
    itens = sorted(os.listdir(caminho))[:50]
    if not itens:
        return f"A pasta {caminho} está vazia."
    return f"Conteúdo de {caminho}:\n" + "\n".join(f"- {i}" for i in itens)


def busca_web(consulta: str) -> str:
    """Busca informações atuais na internet (notícias, previsão do tempo,
    fatos recentes ou qualquer coisa que você não saiba).

    Args:
        consulta: O que buscar, ex.: "previsão do tempo São Paulo amanhã".
    """
    try:
        from ddgs import DDGS
    except ImportError:
        return "Busca web indisponível: instale com 'pip install ddgs'."
    try:
        resultados = DDGS().text(consulta, region="br-pt", max_results=5)
    except Exception as erro:
        return f"Erro na busca: {erro}"
    if not resultados:
        return "Nenhum resultado encontrado."
    linhas = []
    for r in resultados:
        linhas.append(f"- {r.get('title', '')}: {r.get('body', '')} ({r.get('href', '')})")
    return "Resultados da busca:\n" + "\n".join(linhas)


def lembrar(fato: str) -> str:
    """Guarda um fato sobre o usuário na memória permanente do assistente.

    Use quando o usuário mencionar preferências, rotinas, projetos, pessoas
    ou datas importantes que valham a pena lembrar em conversas futuras.

    Args:
        fato: O fato a guardar, em uma frase curta. Ex.: "Prefere café sem açúcar".
    """
    return memoria.lembrar(fato)


def esquecer(trecho: str) -> str:
    """Apaga da memória permanente os fatos que contenham o trecho informado.

    Args:
        trecho: Parte do texto do fato a apagar. Ex.: "café".
    """
    return memoria.esquecer(trecho)


TODAS = [hora_atual, abrir_programa, fechar_programa, abrir_site, listar_arquivos,
         busca_web, lembrar, esquecer]

# Mapa nome -> função, usado pelo main.py para executar as chamadas do modelo
FUNCOES = {f.__name__: f for f in TODAS}
