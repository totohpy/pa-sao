# ai_provider.py — PA Planning Studio
# Unified AI Provider: Vertex AI (Cloud) | Local (Ollama) | On-Premise
# Global session_state — เลือกครั้งเดียวที่หน้าไหนก็ได้ ทุกหน้าใช้ค่าเดิม

import os
import streamlit as st

PROJECT_ID   = os.getenv("GOOGLE_CLOUD_PROJECT", "pa-gen-ai")
LOCATION     = "asia-southeast1"
VERTEX_MODEL = "gemini-1.5-flash-002"

AI_PROVIDER_OPTIONS = {
    "☁️ Cloud AI (Vertex AI)": "vertex",
    "💻 Local AI (Ollama)":    "local",
    "🖥️ On-Premise AI":        "onpremise",
}

def _init_defaults():
    ss = st.session_state
    ss.setdefault("ai_provider",        "vertex")
    ss.setdefault("ai_model",           VERTEX_MODEL)
    ss.setdefault("ai_base_url",        None)
    ss.setdefault("ai_base_url_local",  "http://localhost:11434/v1")
    ss.setdefault("ai_model_local",     "llama3")
    ss.setdefault("ai_base_url_onprem", "http://your-server:8000/v1")
    ss.setdefault("ai_model_onprem",    "typhoon-v2.5-30b-a3b-instruct")
    ss.setdefault("ai_key_onprem",      "")

_init_defaults()


def render_ai_provider_sidebar():
    ss = st.session_state
    _init_defaults()

    st.markdown(
        "<div style='border-top:1px solid rgba(255,255,255,0.18);margin:10px 0 6px;'></div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<span style='color:rgba(255,255,255,0.65);font-size:11px;"
        "font-weight:700;letter-spacing:1px;text-transform:uppercase;'>"
        "⚙️ AI Provider</span>",
        unsafe_allow_html=True,
    )

    current_provider = ss.get("ai_provider", "vertex")
    label_map     = {v: k for k, v in AI_PROVIDER_OPTIONS.items()}
    current_label = label_map.get(current_provider, list(AI_PROVIDER_OPTIONS.keys())[0])
    current_index = list(AI_PROVIDER_OPTIONS.keys()).index(current_label)

    selected_label = st.selectbox(
        "เลือก AI Provider",
        list(AI_PROVIDER_OPTIONS.keys()),
        index=current_index,
        key="ai_provider_select",
        label_visibility="collapsed",
    )
    provider = AI_PROVIDER_OPTIONS[selected_label]
    ss["ai_provider"] = provider

    if provider == "vertex":
        ss["ai_model"]    = VERTEX_MODEL
        ss["ai_base_url"] = None
        st.markdown(
            "<div style='background:rgba(255,255,255,0.10);border-radius:8px;"
            "padding:8px 10px;margin-top:4px;font-size:12px;"
            "color:rgba(255,255,255,0.85);line-height:1.6;'>"
            "✅ <b>Vertex AI</b> · Gemini 1.5 Flash<br>"
            f"<span style='opacity:0.7;'>Project: {PROJECT_ID}</span>"
            "</div>",
            unsafe_allow_html=True,
        )

    elif provider == "local":
        with st.expander("🔧 ตั้งค่า Local AI", expanded=True):
            local_url = st.text_input(
                "Ollama Base URL",
                value=ss.get("ai_base_url_local", "http://localhost:11434/v1"),
                key="ollama_url_input",
                placeholder="http://localhost:11434/v1",
            )
            local_model = st.text_input(
                "Model name",
                value=ss.get("ai_model_local", "llama3"),
                key="ollama_model_input",
                placeholder="llama3 / typhoon2-8b",
            )
            ss["ai_base_url"]       = local_url
            ss["ai_base_url_local"] = local_url
            ss["ai_model"]          = local_model
            ss["ai_model_local"]    = local_model
        st.markdown(
            "<div style='background:rgba(255,255,255,0.10);border-radius:8px;"
            "padding:8px 10px;margin-top:4px;font-size:11.5px;"
            "color:rgba(255,255,255,0.80);line-height:1.65;'>"
            "<b>📥 ติดตั้ง Ollama:</b><br>"
            "1. <a href='https://ollama.com' target='_blank' style='color:#ffd;'>ollama.com</a> → Download<br>"
            "2. รัน: <code style='color:#ffd;'>ollama pull llama3</code><br>"
            "3. URL: <code style='color:#ffd;'>http://localhost:11434/v1</code>"
            "</div>",
            unsafe_allow_html=True,
        )

    elif provider == "onpremise":
        with st.expander("🔧 ตั้งค่า On-Premise AI", expanded=True):
            server_url = st.text_input(
                "Server Base URL",
                value=ss.get("ai_base_url_onprem", "http://your-server:8000/v1"),
                key="onprem_url_input",
                placeholder="http://192.168.x.x:8000/v1",
            )
            server_model = st.text_input(
                "Model name",
                value=ss.get("ai_model_onprem", "typhoon-v2.5-30b-a3b-instruct"),
                key="onprem_model_input",
            )
            server_key = st.text_input(
                "API Key (ถ้ามี)",
                value=ss.get("ai_key_onprem", ""),
                key="onprem_key_input",
                type="password",
                placeholder="ไม่จำเป็น ถ้า server ไม่ต้องการ",
            )
            ss["ai_base_url"]        = server_url
            ss["ai_base_url_onprem"] = server_url
            ss["ai_model"]           = server_model
            ss["ai_model_onprem"]    = server_model
            ss["ai_key_onprem"]      = server_key
        st.markdown(
            "<div style='background:rgba(255,255,255,0.10);border-radius:8px;"
            "padding:8px 10px;margin-top:4px;font-size:11.5px;"
            "color:rgba(255,255,255,0.80);line-height:1.65;'>"
            "<b>🖥️ รองรับ OpenAI-compatible:</b><br>"
            "• vLLM · LM Studio · FastChat"
            "</div>",
            unsafe_allow_html=True,
        )

    return provider


def is_ready() -> bool:
    """True ถ้า provider พร้อมใช้งาน"""
    _init_defaults()
    p = st.session_state.get("ai_provider", "vertex")
    if p == "vertex":
        return True
    url = st.session_state.get("ai_base_url", "")
    return bool(url and str(url).strip())


def get_provider_name() -> str:
    _init_defaults()
    p = st.session_state.get("ai_provider", "vertex")
    if p == "vertex":    return f"☁️ Vertex AI · {VERTEX_MODEL}"
    if p == "local":     return f"💻 Local · {st.session_state.get('ai_model','')}"
    if p == "onpremise": return f"🖥️ On-Premise · {st.session_state.get('ai_model','')}"
    return p


def get_ai_response(
    messages: list,
    system_prompt: str = "",
    temperature: float = 0.7,
    max_tokens: int = 3072,
    stream: bool = False,
):
    _init_defaults()
    provider = st.session_state.get("ai_provider", "vertex")
    full_messages = (
        [{"role": "system", "content": system_prompt}] + messages
        if system_prompt else messages
    )
    if provider == "vertex":
        return _vertex_response(full_messages, temperature, max_tokens, stream)
    else:
        return _openai_compat_response(full_messages, temperature, max_tokens, stream)


def _vertex_response(messages, temperature, max_tokens, stream):
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel, GenerationConfig
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        model = GenerativeModel(VERTEX_MODEL)

        system_parts, user_turn = [], ""
        for msg in messages:
            if msg["role"] == "system":
                system_parts.append(msg["content"])
            elif msg["role"] == "user":
                user_turn = msg["content"]
        if system_parts:
            user_turn = "\n\n".join(system_parts) + "\n\n" + user_turn

        cfg = GenerationConfig(temperature=temperature, max_output_tokens=max_tokens)

        if stream:
            def _gen():
                resp = model.generate_content(user_turn, generation_config=cfg, stream=True)
                for chunk in resp:
                    try: yield chunk.text
                    except Exception: pass
            return _gen()
        else:
            return model.generate_content(user_turn, generation_config=cfg).text

    except ImportError:
        raise RuntimeError("ไม่พบ google-cloud-aiplatform\nติดตั้ง: pip install google-cloud-aiplatform")
    except Exception as e:
        raise RuntimeError(f"Vertex AI error: {e}")


def _openai_compat_response(messages, temperature, max_tokens, stream):
    from openai import OpenAI
    base_url = st.session_state.get("ai_base_url") or "http://localhost:11434/v1"
    model    = st.session_state.get("ai_model")    or "llama3"
    api_key  = st.session_state.get("ai_key_onprem") or "ollama"
    client   = OpenAI(api_key=api_key, base_url=base_url)

    if stream:
        def _gen():
            resp = client.chat.completions.create(
                model=model, messages=messages,
                temperature=temperature, max_tokens=max_tokens, stream=True,
            )
            for chunk in resp:
                delta = chunk.choices[0].delta.content
                if delta: yield delta
        return _gen()
    else:
        resp = client.chat.completions.create(
            model=model, messages=messages,
            temperature=temperature, max_tokens=max_tokens,
        )
        return resp.choices[0].message.content


def ask_ai(prompt: str, system: str = "", temperature: float = 0.7,
           max_tokens: int = 3072) -> str:
    return get_ai_response(
        messages=[{"role": "user", "content": prompt}],
        system_prompt=system, temperature=temperature,
        max_tokens=max_tokens, stream=False,
    )


def provider_badge() -> str:
    _init_defaults()
    p = st.session_state.get("ai_provider", "vertex")
    configs = {
        "vertex":    ("☁️ Cloud AI · Gemini 1.5 Flash", "#1a7f37", "#d4edda"),
        "local":     (f"💻 Local · {st.session_state.get('ai_model','')}", "#0550ae", "#dbeafe"),
        "onpremise": (f"🖥️ On-Premise · {st.session_state.get('ai_model','')}", "#6f42c1", "#f3e8ff"),
    }
    label, color, bg = configs.get(p, configs["vertex"])
    return (
        f"<span style='background:{bg};color:{color};border:1px solid {color}44;"
        f"border-radius:6px;padding:3px 10px;font-size:12px;font-weight:600;'>"
        f"{label}</span>"
    )
