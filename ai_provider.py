# ai_provider.py — PA Planning Studio
# Unified AI Provider: Vertex AI (Cloud) | Local (Ollama) | On-Premise
# ใช้แทน OpenAI client เดิม — ทุกหน้าเรียก get_ai_response() หรือ get_ai_client()

import os
import streamlit as st

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT", "pa-gen-ai")
LOCATION   = "asia-southeast1"
VERTEX_MODEL = "gemini-1.5-flash"

# ── Sidebar UI (เรียกใน theme หรือแต่ละหน้า) ────────────────────────────────
AI_PROVIDER_OPTIONS = {
    "☁️ Cloud AI (Vertex AI)": "vertex",
    "💻 Local AI (Ollama)":    "local",
    "🖥️ On-Premise AI":        "onpremise",
}

def render_ai_provider_sidebar():
    """แสดง UI เลือก AI Provider ใน sidebar — เรียกใน with st.sidebar: block"""
    st.markdown(
        "<div style='border-top:1px solid rgba(255,255,255,0.18);margin:10px 0 6px;'></div>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<span style='color:rgba(255,255,255,0.6);font-size:11px;font-weight:700;"
        "letter-spacing:1px;text-transform:uppercase;'>⚙️ AI Provider</span>",
        unsafe_allow_html=True
    )

    provider_label = st.selectbox(
        "เลือก AI Provider",
        list(AI_PROVIDER_OPTIONS.keys()),
        index=0,
        key="ai_provider_select",
        label_visibility="collapsed",
    )
    provider = AI_PROVIDER_OPTIONS[provider_label]
    st.session_state["ai_provider"] = provider

    # ── Cloud AI ──────────────────────────────────────────────────────────────
    if provider == "vertex":
        st.markdown(
            "<span style='color:rgba(255,255,255,0.75);font-size:12px;'>"
            "✅ ใช้ Vertex AI (Gemini 1.5 Flash)<br>"
            f"Project: <code style='color:#ffd;'>{PROJECT_ID}</code></span>",
            unsafe_allow_html=True,
        )
        st.session_state["ai_base_url"]  = None
        st.session_state["ai_model"]     = VERTEX_MODEL

    # ── Local AI (Ollama) ─────────────────────────────────────────────────────
    elif provider == "local":
        with st.expander("🔧 ตั้งค่า Local AI", expanded=True):
            local_url = st.text_input(
                "Ollama URL",
                value=st.session_state.get("ai_base_url_local", "http://localhost:11434/v1"),
                key="ollama_url_input",
                placeholder="http://localhost:11434/v1",
            )
            local_model = st.text_input(
                "Model name",
                value=st.session_state.get("ai_model_local", "llama3"),
                key="ollama_model_input",
                placeholder="llama3 / typhoon2-8b",
            )
            st.session_state["ai_base_url"]       = local_url
            st.session_state["ai_base_url_local"] = local_url
            st.session_state["ai_model"]          = local_model
            st.session_state["ai_model_local"]    = local_model

        st.markdown(
            """<div style='background:rgba(255,255,255,0.10);border-radius:8px;
            padding:8px 10px;margin-top:4px;font-size:11.5px;color:rgba(255,255,255,0.80);
            line-height:1.65;'>
            <b>📥 ติดตั้ง Ollama:</b><br>
            1. <a href='https://ollama.com' target='_blank'
               style='color:#ffd;'>ollama.com</a> → Download<br>
            2. เปิด Terminal แล้วรัน:<br>
            <code style='color:#ffd;'>ollama pull llama3</code><br>
            หรือ <code style='color:#ffd;'>ollama pull typhoon2-8b</code><br>
            3. ใส่ URL: <code style='color:#ffd;'>http://localhost:11434/v1</code>
            </div>""",
            unsafe_allow_html=True,
        )

    # ── On-Premise AI ─────────────────────────────────────────────────────────
    elif provider == "onpremise":
        with st.expander("🔧 ตั้งค่า On-Premise AI", expanded=True):
            server_url = st.text_input(
                "Server Address (Base URL)",
                value=st.session_state.get("ai_base_url_onprem", "http://your-server-ip:8000/v1"),
                key="onprem_url_input",
                placeholder="http://192.168.x.x:8000/v1",
            )
            server_model = st.text_input(
                "Model name",
                value=st.session_state.get("ai_model_onprem", "typhoon-v2.5-30b-a3b-instruct"),
                key="onprem_model_input",
            )
            server_key = st.text_input(
                "API Key (ถ้ามี)",
                value=st.session_state.get("ai_key_onprem", ""),
                key="onprem_key_input",
                type="password",
                placeholder="ไม่จำเป็น ถ้าเซิร์ฟเวอร์ไม่ต้องการ",
            )
            st.session_state["ai_base_url"]        = server_url
            st.session_state["ai_base_url_onprem"] = server_url
            st.session_state["ai_model"]           = server_model
            st.session_state["ai_model_onprem"]    = server_model
            st.session_state["ai_key_onprem"]      = server_key

        st.markdown(
            """<div style='background:rgba(255,255,255,0.10);border-radius:8px;
            padding:8px 10px;margin-top:4px;font-size:11.5px;color:rgba(255,255,255,0.80);
            line-height:1.65;'>
            <b>🖥️ รองรับ OpenAI-compatible server:</b><br>
            • <b>vLLM</b>: <code style='color:#ffd;'>vllm serve &lt;model&gt;</code><br>
            • <b>LM Studio</b>: เปิด Local Server<br>
            • <b>FastChat / Aphrodite</b><br>
            ใส่ URL + Model name ของ server
            </div>""",
            unsafe_allow_html=True,
        )

    return provider


# ── Core: get_ai_response() ──────────────────────────────────────────────────
def get_ai_response(
    messages: list,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 3072,
    stream: bool = False,
):
    """
    ส่ง messages ไปยัง AI provider ที่เลือก แล้วคืนค่า text response

    Parameters
    ----------
    messages      : list ของ {"role": "user"/"assistant", "content": "..."}
    system_prompt : ข้อความ system (จะ prepend อัตโนมัติ)
    temperature   : ความสุ่มของคำตอบ
    max_tokens    : จำนวน token สูงสุด
    stream        : ถ้า True จะคืน generator (ใช้กับ Streamlit streaming)

    Returns
    -------
    str  (stream=False) หรือ generator ของ str chunks (stream=True)
    """
    provider = st.session_state.get("ai_provider", "vertex")

    if system_prompt:
        full_messages = [{"role": "system", "content": system_prompt}] + messages
    else:
        full_messages = messages

    # ── Vertex AI ────────────────────────────────────────────────────────────
    if provider == "vertex":
        return _vertex_response(full_messages, temperature, max_tokens, stream)

    # ── Local / On-Premise (OpenAI-compatible) ───────────────────────────────
    else:
        return _openai_compat_response(full_messages, temperature, max_tokens, stream)


# ── Vertex AI backend ────────────────────────────────────────────────────────
def _vertex_response(messages, temperature, max_tokens, stream):
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, Content, Part

        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel(VERTEX_MODEL)

        # แปลง messages → Vertex AI format
        history = []
        system_parts = []
        user_turn = ""

        for msg in messages:
            role = msg["role"]
            text = msg["content"]
            if role == "system":
                system_parts.append(text)
            elif role == "user":
                user_turn = text
            elif role == "assistant":
                history.append(Content(role="model",  parts=[Part.from_text(text)]))

        # System prompt รวมเข้าใน user message แรก (Gemini ไม่มี system role)
        if system_parts:
            user_turn = "\n\n".join(system_parts) + "\n\n" + user_turn

        from vertexai.generative_models import GenerationConfig
        gen_cfg = GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)

        if stream:
            def _gen():
                resp = model.generate_content(
                    user_turn, generation_config=gen_cfg, stream=True
                )
                for chunk in resp:
                    try:
                        yield chunk.text
                    except Exception:
                        pass
            return _gen()
        else:
            resp = model.generate_content(user_turn, generation_config=gen_cfg)
            return resp.text

    except ImportError:
        raise RuntimeError(
            "ไม่พบ google-cloud-aiplatform\n"
            "กรุณาติดตั้ง: pip install google-cloud-aiplatform"
        )
    except Exception as e:
        raise RuntimeError(f"Vertex AI error: {e}")


# ── OpenAI-compatible backend (Local / On-Premise) ───────────────────────────
def _openai_compat_response(messages, temperature, max_tokens, stream):
    from openai import OpenAI

    base_url = st.session_state.get("ai_base_url") or "http://localhost:11434/v1"
    model    = st.session_state.get("ai_model")    or "llama3"
    api_key  = st.session_state.get("ai_key_onprem", "ollama") or "ollama"

    client = OpenAI(api_key=api_key, base_url=base_url)

    if stream:
        def _gen():
            resp = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens,
                stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        return _gen()
    else:
        resp = client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        return resp.choices[0].message.content


# ── Convenience: simple single-prompt call ──────────────────────────────────
def ask_ai(prompt: str, system: str = "", temperature: float = 0.7, max_tokens: int = 3072) -> str:
    """Shorthand: ส่ง prompt เดียว แล้วรับ text กลับมา"""
    return get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=False,
    )


# ── Provider status badge (แสดงบนหน้า) ──────────────────────────────────────
def provider_badge() -> str:
    """คืน HTML badge แสดง provider ปัจจุบัน"""
    p = st.session_state.get("ai_provider", "vertex")
    labels = {
        "vertex":    ("☁️ Cloud AI · Gemini 1.5 Flash", "#1a7f37", "#d4edda"),
        "local":     ("💻 Local AI · " + st.session_state.get("ai_model", ""), "#0550ae", "#dbeafe"),
        "onpremise": ("🖥️ On-Premise · " + st.session_state.get("ai_model", ""), "#6f42c1", "#f3e8ff"),
    }
    label, color, bg = labels.get(p, labels["vertex"])
    return (
        f"<span style='background:{bg};color:{color};border:1px solid {color}44;"
        f"border-radius:6px;padding:3px 10px;font-size:12px;font-weight:600;'>"
        f"{label}</span>"
    )
