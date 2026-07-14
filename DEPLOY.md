# Deployment (free)

This app can run **for free** using:

| Platform | RAM | Best for | Guide |
|----------|-----|----------|--------|
| **Hugging Face Spaces** | 16 GB | Full app + PDF/RAG | [deploy/HUGGINGFACE.md](deploy/HUGGINGFACE.md) |
| **Render** | 512 MB | Chat + search only | [deploy/RENDER.md](deploy/RENDER.md) |

Both use the root `Dockerfile` (FastAPI backend + built React UI in one container).

## Quick start (GitHub → Render free)

```powershell
cd "d:\Projects\ai research assistant"
git init
git add .
git commit -m "Prepare for free deployment"
# Create a new empty repo on GitHub, then:
git remote add origin https://github.com/YOUR_USER/ai-research-assistant.git
git branch -M main
git push -u origin main
```

Then follow [deploy/RENDER.md](deploy/RENDER.md) or [deploy/HUGGINGFACE.md](deploy/HUGGINGFACE.md).

## Required secrets (both platforms)

| Variable | Value |
|----------|--------|
| `GROQ_API_KEY` | From [console.groq.com/keys](https://console.groq.com/keys) |
| `LLM_PROVIDER` | `groq` |
| `JWT_SECRET` | Random string (Render can auto-generate) |
| `SERVE_FRONTEND` | `true` |
| `FRONTEND_URL` | Your public app URL (set after first deploy) |

Never commit `.env` — it is gitignored.
