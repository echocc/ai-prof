# 🚀 Quick Deploy to Render.com (5 minutes)

## Prerequisites
- GitHub account
- Render.com account (free)
- Anthropic API key

## Deploy in 3 Steps

### 1️⃣ Push to GitHub
```bash
git init
git add .
git commit -m "Deploy Adyai"
git remote add origin https://github.com/YOUR_USERNAME/adyai-chatbot.git
git push -u origin main
```

### 2️⃣ Deploy on Render
1. Go to [render.com/dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repo
4. Render detects `render.yaml` automatically
5. Click **"Apply"**

### 3️⃣ Add Your API Key
1. Go to **adyai-backend** service
2. Click **"Environment"**
3. Add variable:
   - Key: `ANTHROPIC_API_KEY`
   - Value: `your-api-key`
4. Click **"Save"**

## ✅ Done!

Your app will be live at:
- **Frontend**: `https://adyai-frontend.onrender.com`
- **Backend**: `https://adyai-backend.onrender.com`

## 🗄️ Database Setup

After deployment, you need data:

**Option A - Restore from backup:**
```bash
# Export local DB
pg_dump -U postgres -d ai_prof -f backup.sql

# Import to Render (use connection string from Render dashboard)
psql "postgres://..." < backup.sql
```

**Option B - Re-run ingestion scripts:**
```bash
# SSH into backend service, then run:
python scripts/10_scrape_site.py
python scripts/20_transcribe_audio.py
python scripts/30_ingest_pdfs_epubs.py
python scripts/40_chunk_embed_load.py
```

## 📖 Full Guide
See [DEPLOYMENT.md](./DEPLOYMENT.md) for detailed instructions.

## 💰 Cost
- **Free tier**: 90 days database + 750 hours web services
- **After free**: ~$21/month for all services
- **Cost saver**: Use Claude Haiku model instead of Sonnet

## 🆘 Troubleshooting

**Backend won't start?**
- Check logs in Render dashboard
- Verify `ANTHROPIC_API_KEY` is set
- Ensure database has pgvector: `CREATE EXTENSION vector;`

**Frontend can't reach backend?**
- Check backend is healthy: `/api/health`
- Verify environment variables are set

**Need help?**
- See full deployment guide: [DEPLOYMENT.md](./DEPLOYMENT.md)
- Render docs: https://render.com/docs
