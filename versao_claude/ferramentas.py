"""Ferramentas que o Az pode usar — as "mãos" do assistente.

Cada função com @beta_tool vira automaticamente uma ferramenta que o Claude
pode chamar: o SDK gera o schema a partir da assinatura e da docstring.
Para dar novos poderes ao Az, basta escrever uma função nova aqui e
adicioná-la à lista TODAS no final.
"""

import os
import subprocess
import webbrowser
from datetime import datetime

from anthropic import beta_tool

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


@beta_tool
def hora_atual() -> str:
    """Retorna a data e a hora atuais do computador do usuário."""
    dias = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
            "sexta-feira", "sábado", "domingo"]
    agora = datetime.now()
    return f"{dias[agora.weekday()]}, {agora.strftime('%d/%m/%Y %H:%M:%S')}"


@beta_tool
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


@beta_tool
def abrir_site(url: str) -> str:
    """Abre um site no navegador padrão do usuário.

    Args:
        url: Endereço do site, ex.: "youtube.com" ou "https://github.com".
    """
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Site {url} aberto no navegador."


@beta_tool
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


@beta_tool
def lembrar(fato: str) -> str:
    """Guarda um fato sobre o usuário na memória permanente do assistente.

    Use quando o usuário mencionar preferências, rotinas, projetos, pessoas
    ou datas importantes que valham a pena lembrar em conversas futuras.

    Args:
        fato: O fato a guardar, em uma frase curta. Ex.: "Prefere café sem açúcar".
    """
    return memoria.lembrar(fato)


@beta_tool
def esquecer(trecho: str) -> str:
    """Apaga da memória permanente os fatos que contenham o trecho informado.

    Args:
        trecho: Parte do texto do fato a apagar. Ex.: "café".
    """
    return memoria.esquecer(trecho)


# Busca na web: ferramenta de servidor — roda na infraestrutura da Anthropic,
# não precisa de implementação local.
BUSCA_WEB = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}

TODAS = [hora_atual, abrir_programa, abrir_site, listar_arquivos, lembrar, esquecer, BUSCA_WEB]
