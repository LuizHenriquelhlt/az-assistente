"""Memória persistente do Az: fatos sobre o usuário + histórico de conversas.

Tudo é gravado em um JSON simples em dados/memoria.json. Em um projeto maior
isso viraria um banco de dados com busca semântica (RAG), mas para um
assistente pessoal um arquivo já leva surpreendentemente longe.
"""

import json
import os
from datetime import datetime

from config import PASTA_DADOS, MAX_CONVERSAS_LEMBRADAS

ARQUIVO_MEMORIA = os.path.join(PASTA_DADOS, "memoria.json")


class Memoria:
    def __init__(self):
        self.fatos: list[str] = []
        self.conversas: list[dict] = []
        self._carregar()

    def _carregar(self):
        if os.path.exists(ARQUIVO_MEMORIA):
            with open(ARQUIVO_MEMORIA, "r", encoding="utf-8") as f:
                dados = json.load(f)
            self.fatos = dados.get("fatos", [])
            self.conversas = dados.get("conversas", [])

    def salvar(self):
        os.makedirs(PASTA_DADOS, exist_ok=True)
        with open(ARQUIVO_MEMORIA, "w", encoding="utf-8") as f:
            json.dump(
                {"fatos": self.fatos, "conversas": self.conversas},
                f,
                ensure_ascii=False,
                indent=2,
            )

    # ---- fatos ----

    def lembrar(self, fato: str) -> str:
        fato = fato.strip()
        if fato and fato not in self.fatos:
            self.fatos.append(fato)
            self.salvar()
            return f"Guardado na memória: {fato}"
        return "Eu já sabia disso."

    def esquecer(self, trecho: str) -> str:
        trecho = trecho.strip().lower()
        removidos = [f for f in self.fatos if trecho in f.lower()]
        if not removidos:
            return f"Não encontrei nada na memória contendo '{trecho}'."
        self.fatos = [f for f in self.fatos if trecho not in f.lower()]
        self.salvar()
        return "Esquecido: " + "; ".join(removidos)

    # ---- histórico de conversas ----

    def registrar_conversa(self, usuario: str, assistente: str):
        self.conversas.append(
            {
                "quando": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "usuario": usuario,
                "assistente": assistente[:500],  # resumo, não o texto inteiro
            }
        )
        self.conversas = self.conversas[-MAX_CONVERSAS_LEMBRADAS:]
        self.salvar()

    # ---- contexto injetado no prompt ----

    def contexto(self) -> str:
        """Bloco de texto com o que o Az sabe, anexado ao prompt de sistema.

        Só os fatos entram aqui. Transcrições de conversas antigas ficam de
        fora de propósito: modelos pequenos imitam os exemplos do prompt em
        vez de chamar ferramentas (ex.: repetir uma hora antiga em vez de
        consultar hora_atual). As conversas continuam gravadas no JSON como
        registro.
        """
        if self.fatos:
            return "## O que você sabe sobre o usuário\n" + "\n".join(f"- {f}" for f in self.fatos)
        return ""
