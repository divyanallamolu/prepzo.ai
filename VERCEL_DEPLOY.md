# Vercel deployment checklist (Prepzo API 404 fix)

If `/api/*` returns **404 NOT_FOUND** (Vercel header, not Flask), Python functions are not deployed.

## Required Vercel project settings

1. **Root Directory:** `.` (repository root — must contain `vercel.json` and `api/`)
2. **Framework Preset:** Other (not "Static HTML" only)
3. **Build Command:** leave empty (use `vercel.json`)
4. **Output Directory:** leave empty when using `builds` in `vercel.json`
5. **Install Command:** leave empty (use `vercel.json`)

## Environment variables

| Variable | Required |
|----------|----------|
| `MONGO_URI` | Yes (MongoDB Atlas) |
| `JWT_SECRET_KEY` | Yes |
| `FLASK_SECRET_KEY` | Yes |

## Verify deployment

After deploy, open:

- https://prepzo-ai.vercel.app/api/health → `{"status":"ok",...}`
- https://prepzo-ai.vercel.app/api/companies → JSON array

In Vercel → Deployments → latest → **Functions** tab must list:

- `api/index.py`
- `api/health.py`

If Functions tab is empty, only static files deployed — fix Root Directory / Output Directory overrides.

## Local test (bundled like Vercel)

```bash
cp -r backend api/_backend && cp -r ml api/ml && cp -r database api/database
pip install -r api/requirements.txt
python -c "import importlib.util; s=importlib.util.spec_from_file_location('i','api/index.py'); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); print(m.app.test_client().get('/api/health').json)"
```
