import hmac
import os
from dataclasses import dataclass

import streamlit as st
from openai import OpenAI, OpenAIError


DEFAULT_MODEL = "gpt-5.2"
MANIFEST_INSTRUCTIONS = """Vector store navigation:
- Use `000_vector_store_manifest.md` as the map for this vector store whenever possible.
- Consult the manifest to understand filename prefixes, source authority, expansion assumptions, and whether a file is rules reference material or component fact material.
- Prefer `rules__*`, `rules_factions__*`, and `rules_components__*` for rules interpretation.
- Use `fandom_components__*`, `fandom_factions__*`, `fandom_units__*`, and `fandom_strategy_cards__*` for printed component facts such as card text, faction sheets, starting units, technologies, and unit stats."""
CITATION_INSTRUCTIONS = """Citation requirements:
- Cite every factual rules claim inline, immediately after the claim it supports.
- Prefer source filename plus rule number or section when available, for example: Ships can move during the Move Ships step ([rules__063_movement.md], 58.4).
- If the evidence is uncertain or not found in the available files, say that directly instead of making an uncited claim."""
EXPANSION_CONTEXTS = {
    "All / Unspecified": "This question should assume Twilight Imperium Codex content is included unless the question says otherwise.",
    "Base / Living Rules Reference": (
        "This is a question for the base Twilight Imperium 4th Edition Living Rules Reference rules, "
        "with Twilight Imperium Codex content included unless the question says otherwise."
    ),
    "Prophecy of Kings": (
        "This is a question for the Prophecy of Kings expansion, with Twilight Imperium Codex content included "
        "unless the question says otherwise."
    ),
    "Codices": "This is a question involving Twilight Imperium Codex content.",
    "Thunder’s Edge": (
        "This is a question for the Thunder’s Edge expansion. Assume Prophecy of Kings and Twilight Imperium "
        "Codex content are also included unless the question says otherwise."
    ),
}


@dataclass(frozen=True)
class Source:
    filename: str
    file_id: str


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    vector_store_id: str
    app_password: str
    model: str


def read_secret(name: str, default: str = "") -> str:
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    if value is None:
        value = os.environ.get(name, default)
    return str(value or "")


def load_config() -> tuple[AppConfig, list[str]]:
    config = AppConfig(
        api_key=read_secret("OPENAI_API_KEY"),
        vector_store_id=read_secret("OPENAI_VECTOR_STORE_ID"),
        app_password=read_secret("APP_PASSWORD"),
        model=read_secret("OPENAI_MODEL", DEFAULT_MODEL) or DEFAULT_MODEL,
    )
    missing = [
        name
        for name, value in {
            "OPENAI_API_KEY": config.api_key,
            "OPENAI_VECTOR_STORE_ID": config.vector_store_id,
            "APP_PASSWORD": config.app_password,
        }.items()
        if not value.strip()
    ]
    return config, missing


def password_gate(app_password: str) -> bool:
    if st.session_state.get("authenticated"):
        return True

    with st.form("password_form"):
        entered_password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Unlock")

    if not submitted:
        return False

    if hmac.compare_digest(entered_password, app_password):
        st.session_state["authenticated"] = True
        st.rerun()
    else:
        st.error("Incorrect password.")
    return False


def get_client(api_key: str) -> OpenAI:
    return OpenAI(api_key=api_key)


def build_prompt(user_input: str, expansion_context: str) -> str:
    context_prompt = EXPANSION_CONTEXTS.get(expansion_context, "")
    question = user_input.strip()
    prompt_parts = [part for part in (context_prompt, MANIFEST_INSTRUCTIONS, CITATION_INSTRUCTIONS, question) if part]
    return "\n\n".join(prompt_parts)


def collect_sources(response) -> list[Source]:
    sources: list[Source] = []
    seen: set[tuple[str, str]] = set()

    def add_source(filename: str | None, file_id: str | None) -> None:
        if not filename and not file_id:
            return
        source = Source(filename=filename or "Untitled file", file_id=file_id or "unknown")
        key = (source.filename, source.file_id)
        if key not in seen:
            seen.add(key)
            sources.append(source)

    for output_item in getattr(response, "output", []) or []:
        if getattr(output_item, "type", None) == "message":
            for content_item in getattr(output_item, "content", []) or []:
                for annotation in getattr(content_item, "annotations", []) or []:
                    if getattr(annotation, "type", None) in {"file_citation", "container_file_citation"}:
                        add_source(getattr(annotation, "filename", None), getattr(annotation, "file_id", None))

    return sources


def ask_rules_question(
    *,
    api_key: str,
    vector_store_id: str,
    model: str,
    user_input: str,
) -> tuple[str, list[Source]]:
    client = get_client(api_key)
    response = client.responses.create(
        model=model,
        input=user_input,
        include=["file_search_call.results"],
        tools=[
            {
                "type": "file_search",
                "vector_store_ids": [vector_store_id],
            }
        ],
    )
    return response.output_text, collect_sources(response)


st.set_page_config(page_title="TI4 Rules GPT", page_icon="📘", layout="centered")

st.title("TI4 Rules GPT")
st.caption("Ask questions against the TI4 rules vector store.")

config, missing_settings = load_config()
if missing_settings:
    st.error("App configuration is incomplete. Ask the app owner to configure Streamlit secrets.")
    st.info("Missing secret(s): " + ", ".join(missing_settings))
    st.stop()

if not password_gate(config.app_password):
    st.stop()

with st.sidebar:
    st.header("Rules Context")
    expansion_context = st.selectbox("Rules context", options=list(EXPANSION_CONTEXTS))
    if st.button("Lock app"):
        st.session_state["authenticated"] = False
        st.rerun()

user_input = st.text_area(
    "Question",
    placeholder="Example: How do I set up objectives during setup?",
    height=160,
)

submit = st.button("Ask", type="primary", disabled=not user_input.strip())

if submit:
    with st.spinner("Searching the vector store..."):
        try:
            prompt = build_prompt(user_input, expansion_context)
            answer, sources = ask_rules_question(
                api_key=config.api_key,
                vector_store_id=config.vector_store_id,
                model=config.model,
                user_input=prompt,
            )
        except OpenAIError as exc:
            st.error(f"OpenAI API error: {exc}")
        except Exception as exc:
            st.error(f"Unexpected error: {exc}")
        else:
            st.subheader("Answer")
            st.markdown(answer)
            st.subheader("Cited files")
            if sources:
                for source in sources:
                    st.markdown(f"- `{source.filename}` (`{source.file_id}`)")
            else:
                st.caption("No citation annotations were returned; rely on the inline citations in the answer.")
