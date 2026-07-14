# Deploy free on Hugging Face Spaces (recommended)

HF **CPU Basic** spaces are **free** with **16 GB RAM** — enough for chat, web search, PDF upload, and RAG.

## Steps

1. Create a Hugging Face account: [huggingface.co/join](https://huggingface.co/join)

2. Create a new **Space**:
   - [huggingface.co/new-space](https://huggingface.co/new-space)
   - **Space SDK**: Docker
   - **Visibility**: Public (required for free hardware)
   - **Hardware**: CPU basic (free)

3. Clone the Space repo and copy this project in, **or** push from GitHub:
   - In Space settings → **Repository** → link GitHub repo

4. Ensure the Space `README.md` starts with this frontmatter (create/replace in the Space repo root):

```yaml
---
title: AI Research Assistant
emoji: 🔬
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8000
pinned: false
---
```

5. Add **Secrets** in Space → Settings → Repository secrets:
   - `GROQ_API_KEY` = your Groq key
   - `LLM_PROVIDER` = `groq`
   - `GROQ_MODEL` = `llama-3.3-70b-versatile`
   - `SERVE_FRONTEND` = `true`
   - `JWT_SECRET` = a long random string
   - `FRONTEND_URL` = your Space URL, e.g. `https://YOUR-USER-ai-research-assistant.hf.space`

6. The Space builds from the root `Dockerfile`. When status is **Running**, open the Space URL.

## Notes

- Spaces sleep when idle; first load may take a minute.
- Data (SQLite/Chroma) is ephemeral unless you add paid persistent storage.
- LLM usage stays free via Groq’s free tier (rate limits apply).
