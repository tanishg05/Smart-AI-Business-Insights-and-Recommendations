# Deploying: frontend on Vercel, backend on Render

The React frontend is a static site, so it fits Vercel perfectly. The FastAPI backend keeps the
loaded dataset **in memory** between requests and streams copilot answers, so it needs a
long-running server. Render's free web service gives you that; Vercel's Python functions do not
(see "Why not put the backend on Vercel too?" at the end).

```
Browser ──> Vercel (frontend/dist, static)
   │
   └── HTTPS ──> Render (uvicorn app:app) ──> Groq API
                     └─ loads backend/uploads/fmcg_clean.csv at start-up
```

Everything the hosts need is already in the repo:

| File | Used by | What it does |
| --- | --- | --- |
| `render.yaml` | Render | Python 3.11, `pip install -r requirements.txt`, `uvicorn app:app --port $PORT`, health check, env vars |
| `frontend/vercel.json` | Vercel | Vite build, output `dist/` |
| `backend/uploads/fmcg_clean.csv` | Render | Reference dataset loaded at start-up (`DEFAULT_DATASET`) |
| `BACKEND_CORS_ORIGINS` / `BACKEND_CORS_ORIGIN_REGEX` | backend | Which website origins may call the API |
| `VITE_API_BASE_URL` | frontend build | Where the frontend finds the API |

## 1. Put the code on GitHub

Both hosts deploy from a Git repository. Create an **empty private** repository on github.com
(no README), then from the DVP folder:

```bash
git remote add origin https://github.com/<you>/supply-chain-dashboard.git
git push -u origin main
```

`backend/.env` (your Groq key) is git-ignored and is never pushed.

## 2. Deploy the backend on Render

1. Sign in at https://dashboard.render.com with GitHub.
2. **New → Blueprint**, pick the repository. Render reads `render.yaml` and proposes the
   `supply-chain-api` service.
3. Fill in the secret values it asks for:
   - `GROQ_API_KEY`: your `gsk_…` key. **The key belongs here, on the backend, not on Vercel.**
   - `BACKEND_CORS_ORIGINS`: leave `http://localhost:3000` for now; you'll set the Vercel URL in step 4.
   - `BACKEND_CORS_ORIGIN_REGEX`: leave empty for now.
4. **Apply**. The first build takes a few minutes (pandas and numpy).
5. Open `https://<your-service>.onrender.com/health`. You should see
   `{"status":"ok","dataset_loaded":true}`. Copy this base URL.

## 3. Deploy the frontend on Vercel

1. Sign in at https://vercel.com with GitHub. **Add New → Project**, import the repository.
2. Set **Root Directory** to `frontend`. Vercel detects Vite and uses `frontend/vercel.json`.
3. Under **Environment Variables** add:
   - `VITE_API_BASE_URL` = `https://<your-service>.onrender.com` (no trailing slash)
4. **Deploy**. Copy the production URL, for example `https://supply-chain-dashboard.vercel.app`.

`VITE_` variables are baked into the JavaScript at build time and are visible to anyone who opens
the site. Never put `GROQ_API_KEY` in Vercel.

## 4. Connect the two

1. In Render → your service → **Environment**, set
   - `BACKEND_CORS_ORIGINS` = your Vercel production URL
   - optionally `BACKEND_CORS_ORIGIN_REGEX` = `^https://supply-chain-dashboard.*\.vercel\.app$`
     so Vercel preview deployments work too.
2. Save; Render redeploys.
3. Open the Vercel URL. The Overview should load with fmcg_clean.csv, and the copilot pill should
   show `openai/gpt-oss-120b` with a green dot.

From now on, every `git push` redeploys both sides automatically.

## What to expect on the free plans

- **Cold starts.** A free Render service goes to sleep after about 15 minutes without traffic.
  The next visit wakes it, which can take up to a minute while it also reloads the CSV.
- **Uploads are temporary.** Files uploaded through the dashboard live on the server's disk only
  until the next restart or deploy. `fmcg_clean.csv` comes back automatically because it is in the repo.
- **One shared dataset.** The backend holds one dataset in memory for everyone. If one visitor
  uploads a file, every visitor sees it until the next restart.
- **Memory.** The FMCG dataset uses well under the free plan's 512 MB.

## Why not put the backend on Vercel too?

Vercel can run Python, but as serverless functions: each request may land on a fresh instance with
an empty memory and a read-only disk (apart from `/tmp`). For this backend that means every cold
request re-reads and re-processes the 19 MB CSV, uploads vanish between requests, and pandas plus
NumPy take most of the function size budget. Making it work there would need a rewrite to store the
dataset outside the process (for example in object storage) and recompute per request.

## Updating the Groq key or model

Render → service → **Environment** → edit `GROQ_API_KEY` or `GROQ_MODEL` → save. The service
restarts with the new value; nothing needs to be rebuilt on Vercel.
