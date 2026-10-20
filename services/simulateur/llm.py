





import hashlib
import json
import os
import re
import urllib.request

URL = "https://nano-gpt.com/api/v1/chat/completions"
_cache: dict = {}


def _config() -> dict:
    cfg = {k: os.environ[k] for k in ("NANOGPT_API_KEY", "NANOGPT_MODEL") if k in os.environ}
    chemin = os.path.expanduser("~/.config/alpha/nanogpt.env")
    if os.path.exists(chemin):
        with open(chemin, encoding="utf-8") as f:
            for ligne in f:
                if "=" in ligne and not ligne.startswith("#"):
                    cle, valeur = ligne.strip().split("=", 1)
                    cfg.setdefault(cle, valeur)
    return cfg


def actif() -> bool:
    return os.environ.get("SIM_LLM") == "1" and "NANOGPT_API_KEY" in _config()


def discuter(messages: list, max_tokens: int = 250, temperature: float = 0.2, timeout: float = 25.0) -> str:



    if messages and messages[0]["role"] == "system":
        messages = [{"role": "user", "content": messages[0]["content"] + "\n\n" + messages[1]["content"]}] + list(messages[2:])
    empreinte = hashlib.sha256(json.dumps(messages, sort_keys=True).encode()).hexdigest()
    if empreinte in _cache:
        return _cache[empreinte]
    cfg = _config()
    corps = {"model": cfg.get("NANOGPT_MODEL", "qwen/qwen3.8-27b-cybersecurity"), "messages": messages,
             "max_tokens": max_tokens, "temperature": temperature}
    requete = urllib.request.Request(URL, data=json.dumps(corps).encode(), method="POST", headers={
        "Content-Type": "application/json", "Authorization": "Bearer " + cfg["NANOGPT_API_KEY"]})
    with urllib.request.urlopen(requete, timeout=timeout) as r:
        texte = json.load(r)["choices"][0]["message"]["content"]
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.S).strip()
    _cache[empreinte] = texte
    return texte
