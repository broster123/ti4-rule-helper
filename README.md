# TI4 Rules GPT Streamlit App

Deployment folder for Streamlit Community Cloud.

## Streamlit Secrets

Configure these secrets in Streamlit Community Cloud:

```toml
OPENAI_API_KEY = "..."
OPENAI_VECTOR_STORE_ID = "..."
APP_PASSWORD = "..."
OPENAI_MODEL = "gpt-5.2"
```

`OPENAI_MODEL` is optional. The app defaults to `gpt-5.2`.

## Local Run

For local development, use environment variables with the same names:

```bash
export OPENAI_API_KEY="..."
export OPENAI_VECTOR_STORE_ID="..."
export APP_PASSWORD="..."
export OPENAI_MODEL="gpt-5.2"
streamlit run streamlit_app.py
```

The app requires the password before it shows the question UI or calls OpenAI.

## Safety

Never commit `.streamlit/secrets.toml`, `.env`, or real API keys. If a key has appeared in shell history or chat logs, rotate it before deploying.
