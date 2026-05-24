<<<<<<< HEAD
# 🎈 Blank app template

A simple Streamlit app template for you to modify!

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://blank-app-template.streamlit.app/)

### How to run it on your own machine

1. Install the requirements

   ```
   $ pip install -r requirements.txt
   ```

2. Run the app

   ```
   $ streamlit run streamlit_app.py
   ```
=======
# TI4 Rules GPT Streamlit App

Deployment folder for Streamlit Community Cloud.

## Streamlit Secrets

Configure these secrets in Streamlit Community Cloud:

```toml
OPENAI_API_KEY = "..."
OPENAI_VECTOR_STORE_ID = "..."
APP_PASSWORD = "..."
OPENAI_MODEL = "gpt-5.5"
```

`OPENAI_MODEL` is optional. The app defaults to `gpt-5.5`.

## Local Run

For local development, use environment variables with the same names:

```bash
export OPENAI_API_KEY="..."
export OPENAI_VECTOR_STORE_ID="..."
export APP_PASSWORD="..."
export OPENAI_MODEL="gpt-5.5"
streamlit run main.py
```

The app requires the password before it shows the question UI or calls OpenAI.

## Safety

Never commit `.streamlit/secrets.toml`, `.env`, or real API keys. If a key has appeared in shell history or chat logs, rotate it before deploying.
>>>>>>> d05bb05 (Add Streamlit Cloud deployment app)
