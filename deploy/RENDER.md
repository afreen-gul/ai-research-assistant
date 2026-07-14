# Deploy completely on Render (free)

One Render service hosts **both** the React UI and the FastAPI backend — simplest setup.

## Free tier limits

| Limit | Impact |
|-------|--------|
| **512 MB RAM** | Chat + web search usually work. PDF upload / RAG may fail or crash (embeddings need ~400MB+). |
| **Sleeps after ~15 min idle** | First visit after sleep takes ~30–60 seconds. |
| **No persistent disk** | Sessions, notes, and uploads reset on redeploy/restart. |
| **750 hours/month** | Enough for one app running 24/7. |

## Step-by-step

### 1. Push code to GitHub

Repo: [github.com/afreen-gul/ai-research-assistant](https://github.com/afreen-gul/ai-research-assistant)

### 2. Create Render Blueprint

1. Go to [render.com](https://render.com) → sign in with GitHub
2. **New** → **Blueprint**
3. Connect **`afreen-gul/ai-research-assistant`**
4. Render reads `render.yaml` (full `Dockerfile`, UI + API together)

### 3. Set secrets

When prompted:

| Key | Value |
|-----|--------|
| `GROQ_API_KEY` | Your key from [console.groq.com/keys](https://console.groq.com/keys) |
| `FRONTEND_URL` | Leave blank for now |

### 4. Deploy

1. Click **Apply**
2. Wait **10–20 minutes** (first Docker build installs PyTorch + embedding model)
3. When status is **Live**, copy your URL, e.g. `https://ai-research-assistant.onrender.com`

### 5. Set FRONTEND_URL

1. Render → your service → **Environment**
2. Add `FRONTEND_URL` = same URL, e.g. `https://ai-research-assistant.onrender.com`
3. Save (auto-restarts)

### 6. Test

1. Open your `*.onrender.com` URL — you should see the chat UI
2. Send: *"What is machine learning?"*
3. Check health: `https://YOUR-URL.onrender.com/api/health`

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails / **Out of memory** | Free tier too small for full app — use HF Static + Render split, or Render paid tier |
| **GROQ_API_KEY not configured** | Add in Environment → redeploy |
| Blank page | Confirm `SERVE_FRONTEND=true` in Environment |
| Slow first load | Normal — free tier waking from sleep |
| PDF upload fails | Expected on 512 MB — chat-only mode still works |

## Render-only vs split (HF + Render)

| | **Render only** | **HF Static + Render** |
|---|---|---|
| Setup | Easier — one URL | Two platforms |
| UI hosting | Render | Hugging Face (free Static) |
| API hosting | Render | Render |
| Best for | Quick demo, chat + search | Same, but UI always free on HF |

Both stay **$0** on free tiers.
