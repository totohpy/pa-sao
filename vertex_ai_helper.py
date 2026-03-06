"""
vertex_ai_helper.py
-------------------
Helper module สำหรับเรียกใช้ Vertex AI Gemini 1.5 Flash
ใช้ร่วมกันทุกหน้าใน PA Studio
"""
import streamlit as st
import os
from typing import Generator

# ── Lazy imports เพื่อ startup เร็ว ──────────────────
_vertexai      = None
_GenerativeModel = None
_service_account = None

def _init_vertex():
    """เรียกครั้งแรกเท่านั้น — init Vertex AI จาก secret หรือ ADC"""
    global _vertexai, _GenerativeModel, _service_account

    if _vertexai is not None:
        return  # already initialized

    import vertexai
    from vertexai.generative_models import GenerativeModel
    from google.oauth2 import service_account as sa

    _vertexai        = vertexai
    _GenerativeModel = GenerativeModel
    _service_account = sa

    # ── Load credentials ──────────────────────────────
    # วิธี 1: Streamlit secrets (local dev / Streamlit Cloud)
    try:
        sa_info = dict(st.secrets["gcp_service_account"])
        creds   = sa.Credentials.from_service_account_info(
            sa_info,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        project_id = sa_info["project_id"]
    except Exception:
        # วิธี 2: Application Default Credentials (Cloud Run — Workload Identity)
        creds      = None   # ใช้ ADC อัตโนมัติ
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")

    vertexai.init(
        project=project_id,
        location="asia-southeast1",   # Singapore
        credentials=creds
    )


def chat(system_prompt: str, user_prompt: str,
         temperature: float = 0.7,
         max_output_tokens: int = 2048) -> str:
    """
    ส่ง prompt ไป Gemini 1.5 Flash และรับ text กลับ (non-streaming)
    ใช้สำหรับ: 6W2H, Audit Plan Generator, Audit Design Assistant
    """
    _init_vertex()
    model = _GenerativeModel(
        "gemini-1.5-flash-001",
        system_instruction=system_prompt
    )
    resp = model.generate_content(
        user_prompt,
        generation_config={
            "temperature":        temperature,
            "max_output_tokens":  max_output_tokens,
            "top_p":              0.9,
        }
    )
    return resp.text


def chat_stream(system_prompt: str, user_prompt: str,
                max_output_tokens: int = 2048) -> Generator:
    """
    Streaming version — ใช้สำหรับ PA Assistant Chat
    yield text chunk ทีละก้อน
    """
    _init_vertex()
    model = _GenerativeModel(
        "gemini-1.5-flash-001",
        system_instruction=system_prompt
    )
    stream = model.generate_content(
        user_prompt,
        generation_config={
            "temperature":       0.7,
            "max_output_tokens": max_output_tokens,
        },
        stream=True
    )
    for chunk in stream:
        try:
            if chunk.text:
                yield chunk.text
        except Exception:
            continue


def is_available() -> bool:
    """ตรวจว่า Vertex AI ใช้ได้หรือไม่ (มี secret หรือ ADC)"""
    try:
        _init_vertex()
        return True
    except Exception:
        return False
