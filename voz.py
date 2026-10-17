"""Módulo de voz do Az: wake word, ouvir pelo microfone e falar em voz alta.

Fala com dois níveis:
  1. Voz neural (edge-tts + pygame) — quase humana, precisa de internet
  2. Voz do Windows (pyttsx3) — robótica, offline; usada como fallback

Wake word: o Az fica em espera e só processa comandos depois de ouvir "Ei Az"
(com tolerância a variações de transcrição, ex.: "ei às", "hey az").

Dependências: pip install SpeechRecognition pyaudio edge-tts pygame pyttsx3
Se não estiverem instaladas, o Az funciona normalmente em modo texto.
"""

import asyncio
import os
import re
import tempfile
import unicodedata

from config import VOZ_NEURAL, MICROFONE_INDICE

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

try:
    import speech_recognition as sr

    DISPONIVEL = True
except ImportError:
    DISPONIVEL = False

try:
    import edge_tts
    import pygame

    NEURAL_DISPONIVEL = True
except ImportError:
    NEURAL_DISPONIVEL = False

try:
    import pyttsx3

    OFFLINE_DISPONIVEL = True
except ImportError:
    OFFLINE_DISPONIVEL = False

_motor_fala = None


# ---------- wake word ----------

# "Az" é curto demais para o reconhecedor: na prática chega como "as", "às",
# "a z", "ez"... A regra: a frase começou com o nome (ou com uma chamada tipo
# "ei az"), acordou — e o que vier depois é o comando.
_CHAMADAS = {"ei", "hei", "hey", "oi", "eiaz", "eias", "heyaz", "eia", "ea", "eaz"}
_NOMES = {"az", "as", "ez", "es", "haz", "azz", "a", "z", "ah", "ha"}
# Formas que valem como "Az" dito sozinho, no começo da frase ("a" sozinho
# fica de fora por ser comum demais; "a z" é tratado à parte)
_NOMES_FORTES = {"az", "as", "ez", "es", "haz", "azz", "has",
                 "piaz", "pias", "iaz", "ias", "eaz", "eias"}


def _normalizar(palavra: str) -> str:
    palavra = unicodedata.normalize("NFD", palavra.lower())
    palavra = "".join(c for c in palavra if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", palavra)


def extrair_comando_wake(texto: str) -> str | None:
    """Verifica se a frase começa com o wake word.

    Retorna o comando que vem depois ("" se a pessoa só chamou o Az),
    ou None se o wake word não foi dito.
    """
    pares = [(_normalizar(p), p) for p in texto.split()]
    pares = [(n, p) for n, p in pares if n]
    if not pares:
        return None
    if pares[0][0] in _CHAMADAS:
        # "ei az ..." — descarta até 2 pedaços do nome após a chamada
        i = 1
        while i < len(pares) and i <= 2 and pares[i][0] in _NOMES:
            i += 1
    elif pares[0][0] in _NOMES_FORTES:
        # "az ..." — o nome sozinho já acorda
        i = 1
    elif pares[0][0] == "a" and len(pares) >= 2 and pares[1][0] == "z":
        # "a z ..." — transcrição soletrada do nome
        i = 2
    else:
        return None
    return " ".join(p for _, p in pares[i:]).strip(" ,.!?")


def _bip():
    """Som curto confirmando que o Az acordou."""
    try:
        import winsound

        winsound.Beep(950, 180)
    except Exception:
        pass


def aguardar_wake() -> str | None:
    """Fica ouvindo até alguém dizer "Ei Az".

    Se o comando vier junto ("Ei Az, que horas são?"), retorna o comando.
    Se for só o chamado, dá um bipe e escuta o comando em seguida.
    Retorna None se o comando não foi entendido (o chamador decide repetir).
    """
    print("💤 Aguardando 'Az'...")
    while True:
        texto = ouvir(aviso=None, limite_frase=6, log_incompreensivel=True)
        if not texto:
            continue
        comando = extrair_comando_wake(texto)
        if comando is None:
            print(f"💤 (ouvi {texto!r} — não era pra mim)")
            continue
        if comando:
            print(f"Você: Ei Az, {comando}")
            return comando
        _bip()
        comando = ouvir(aviso="🎤 Pode falar...")
        if comando:
            print(f"Você: {comando}")
        return comando


# ---------- ouvir ----------

# Um único reconhecedor, calibrado uma vez só: recalibrar a cada ciclo criava
# uma "zona morta" de ~0,4s em que a fala era perdida. O ajuste dinâmico de
# energia continua ativo e vai se adaptando ao ambiente sozinho.
_reconhecedor = None


def _obter_reconhecedor():
    global _reconhecedor
    if _reconhecedor is None:
        _reconhecedor = sr.Recognizer()
        _reconhecedor.dynamic_energy_threshold = True
        with sr.Microphone(device_index=MICROFONE_INDICE) as fonte:
            _reconhecedor.adjust_for_ambient_noise(fonte, duration=1.0)
        # piso no limiar: impede que ruído de fundo dispare capturas em série
        _reconhecedor.energy_threshold = max(_reconhecedor.energy_threshold, 800)
        # sem ajuste dinâmico: em ambiente barulhento ele vai baixando o limiar
        # sozinho até o ruído virar "fala" — melhor manter fixo
        _reconhecedor.dynamic_energy_threshold = False
    return _reconhecedor


def ouvir(timeout: float = 8.0, aviso: str | None = "🎤 Ouvindo...",
          limite_frase: float = 15.0, log_incompreensivel: bool = False) -> str | None:
    """Escuta o microfone e retorna o texto reconhecido (ou None)."""
    reconhecedor = _obter_reconhecedor()
    with sr.Microphone(device_index=MICROFONE_INDICE) as fonte:
        if aviso:
            print(aviso)
        try:
            audio = reconhecedor.listen(fonte, timeout=timeout,
                                        phrase_time_limit=limite_frase)
        except sr.WaitTimeoutError:
            return None
    try:
        return reconhecedor.recognize_google(audio, language="pt-BR")
    except sr.UnknownValueError:
        if log_incompreensivel:
            print("💤 (captei um som, mas não entendi as palavras)")
        return None
    except sr.RequestError as erro:
        print(f"⚠️ Erro no serviço de reconhecimento: {erro}")
        return None


# ---------- falar ----------

def falar(texto: str):
    """Lê o texto em voz alta: tenta a voz neural, cai pra offline se falhar."""
    if not texto.strip():
        return
    if NEURAL_DISPONIVEL and _falar_neural(texto):
        return
    if OFFLINE_DISPONIVEL:
        _falar_offline(texto)


def _falar_neural(texto: str) -> bool:
    try:
        caminho = os.path.join(tempfile.gettempdir(), "az_fala.mp3")
        asyncio.run(edge_tts.Communicate(texto, VOZ_NEURAL).save(caminho))

        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(caminho)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.wait(100)
        pygame.mixer.music.unload()
        return True
    except Exception:
        return False  # sem internet ou erro de áudio -> fallback offline


def _falar_offline(texto: str):
    global _motor_fala
    if _motor_fala is None:
        _motor_fala = pyttsx3.init()
        for voz in _motor_fala.getProperty("voices"):
            if "brazil" in voz.name.lower() or "portug" in voz.name.lower():
                _motor_fala.setProperty("voice", voz.id)
                break
        _motor_fala.setProperty("rate", 180)
    _motor_fala.say(texto)
    _motor_fala.runAndWait()
