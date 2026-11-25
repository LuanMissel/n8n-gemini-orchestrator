import os
from typing import Any
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import requests

load_dotenv()

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "").strip()

app = FastAPI(
    title="API Integração n8n + IA",
    description="API em FastAPI que valida mensagens e envia para o fluxo de automação no n8n.",
    version="1.0.0",
)


class MensagemEntrada(BaseModel):
    mensagem: str = Field(..., min_length=1, description="Conteúdo principal da mensagem")
    pergunta: str | None = None
    contexto: str | None = None
    categoria: str | None = None
    filtros: dict[str, Any] | None = None


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/processar")
def processar_mensagem(payload: MensagemEntrada):
    if not N8N_WEBHOOK_URL:
        raise HTTPException(
            status_code=500,
            detail="Variável N8N_WEBHOOK_URL não configurada no ambiente.",
        )

    # Remove campos None para enviar um JSON limpo ao n8n
    dados_envio = payload.model_dump(exclude_none=True)

    try:
        resp = requests.post(N8N_WEBHOOK_URL, json=dados_envio, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Tempo limite excedido ao chamar o n8n.")
    except requests.exceptions.RequestException as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Erro de comunicação com o webhook do n8n: {exc}",
        )

    try:
        resultado_n8n = resp.json()
    except ValueError:
        resultado_n8n = {"resposta_texto": resp.text}

    return {
        "status": "sucesso",
        "dados_enviados": dados_envio,
        "resultado_n8n": resultado_n8n,
    }