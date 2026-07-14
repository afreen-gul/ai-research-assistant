# Deploy free on Render

Render’s **free web service** hosts the full app (API + React UI) from one Docker container.

## Limits (free tier)

- **512 MB RAM** — may be tight for PDF/RAG (local embeddings). Chat + web search usually works.
- **Sleeps after ~15 min idle** — first request after sleep takes ~30–60s to wake.
- **No persistent disk** — sessions/notes reset when the service redeploys or restarts.

For more RAM (16 GB) on free tier, use [Hugging Face Spaces](./HUGGINGFACE.md) instead.

## Steps

1. **Push this repo to GitHub** (see root `DEPLOY.md`).

2. Open [render.com](https://render.com) → **New** → **Blueprint** → connect your GitHub repo.

3. Render reads `render.yaml` automatically.

4. When prompted, set secrets:
   - `GROQ_API_KEY` — your key from [console.groq.com/keys](https://console.groq.com/keys)
   - `FRONTEND_URL` — your app URL after first deploy, e.g. `https://ai-research-assistant.onrender.com`

5. Click **Apply**. First build takes ~10–15 minutes (PyTorch + embedding model).

6. Open your `*.onrender.com` URL and test chat.

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails / OOM | Use Hugging Face Spaces (more RAM) |
| “GROQ_API_KEY not configured” | Add secret in Render → Environment |
| Slow first request | Free tier cold start — wait ~1 min |
| Data lost after redeploy | Expected on free tier (no disk) |
