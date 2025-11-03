# Adyai Deployment Guide - Render.com

Complete guide to deploying Adyai chatbot to production on Render.com (free tier).

## 📋 Prerequisites

Before deploying, make sure you have:
- [x] GitHub account
- [x] Render.com account (free) - [Sign up here](https://render.com)
- [x] Anthropic API key
- [x] Your code pushed to GitHub

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Initialize Git** (if not already done):
```bash
cd /Users/echo/ai-prof
git init
git add .
git commit -m "Initial commit - Adyai chatbot"
```

2. **Create GitHub Repository**:
   - Go to [github.com/new](https://github.com/new)
   - Create a new repository (e.g., `adyai-chatbot`)
   - Don't initialize with README (we already have code)

3. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/adyai-chatbot.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy Database to Render

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"PostgreSQL"**
3. Configure:
   - **Name**: `adyai-postgres`
   - **Database**: `ai_prof`
   - **User**: `postgres`
   - **Region**: Choose closest to you
   - **PostgreSQL Version**: **14**
   - **Plan**: **Free**
4. Click **"Create Database"**
5. Wait for provisioning (~2-3 minutes)

### Step 3: Install pgvector Extension

1. Once database is ready, go to database dashboard
2. Click **"Connect"** → **"External Connection"**
3. Copy the **"PSQL Command"**
4. Run in your terminal:
```bash
# Paste the PSQL command from Render, then run:
CREATE EXTENSION IF NOT EXISTS vector;
\q
```

### Step 4: Restore Your Database

You need to copy your local database to Render:

```bash
# 1. Export your local database
pg_dump -U postgres -d ai_prof -f adyai_backup.sql

# 2. Import to Render (use the external connection string from Render)
psql "postgres://USER:PASSWORD@HOST/DATABASE" < adyai_backup.sql
```

**Alternative**: Re-run your ingestion scripts on Render (see Step 7)

### Step 5: Deploy Using Render Blueprint

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render will automatically detect `render.yaml`
5. Review the services:
   - ✅ `adyai-postgres` (database)
   - ✅ `adyai-backend` (FastAPI)
   - ✅ `adyai-frontend` (Next.js)

6. Click **"Apply"**

### Step 6: Configure Environment Variables

**For adyai-backend service:**

1. Go to backend service dashboard
2. Click **"Environment"** tab
3. Add **`ANTHROPIC_API_KEY`**:
   - Key: `ANTHROPIC_API_KEY`
   - Value: `your-api-key-here`
   - Click **"Save Changes"**

The service will automatically redeploy.

### Step 7: Wait for Deployment

Monitor the deployment:
- **Backend**: ~5-10 minutes (installing Python dependencies)
- **Frontend**: ~3-5 minutes (building Next.js)
- **Database**: Already running

You can watch logs in real-time for each service.

### Step 8: Test Your Deployment

1. **Check Backend Health**:
   - Go to backend URL: `https://adyai-backend.onrender.com/api/health`
   - Should return: `{"status":"healthy",...}`

2. **Check Frontend**:
   - Go to frontend URL: `https://adyai-frontend.onrender.com`
   - Should see the Adyai chatbot interface

3. **Test a Query**:
   - Type a question like "What is awakening?"
   - Verify you get a response with sources

## ⚙️ Configuration

### Environment Variables

**Backend (.env on Render)**:
```
DATABASE_URL=<auto-set by Render>
ANTHROPIC_API_KEY=<your-api-key>
EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
TOKENIZERS_PARALLELISM=false
```

**Frontend (.env on Render)**:
```
NEXT_PUBLIC_API_URL=<auto-set by Render>
```

### Custom Domains (Optional)

1. Go to service settings
2. Click **"Custom Domains"**
3. Add your domain (e.g., `adyai.yourdomain.com`)
4. Update DNS records as instructed

## 🔧 Troubleshooting

### Backend Fails to Start

**Error: "No module named 'xxx'"**
- Check `requirements.txt` has all dependencies
- Force rebuild: Settings → Manual Deploy → Clear Build Cache

**Error: "pgvector extension not found"**
- Run `CREATE EXTENSION vector;` in database
- Ensure PostgreSQL version is 14+

### Frontend Can't Connect to Backend

**Error: "500 Internal Server Error"**
- Check backend is healthy: `/api/health`
- Verify `ANTHROPIC_API_KEY` is set
- Check backend logs for errors

**Error: "Network Error"**
- Check `NEXT_PUBLIC_API_URL` environment variable
- Ensure backend service is running

### Database Connection Issues

**Error: "Connection refused"**
- Verify `DATABASE_URL` is set correctly
- Check database is running (green status)
- Ensure pgvector extension is installed

## 💰 Cost Breakdown

### Free Tier Limits
- **PostgreSQL**: 90 days free, then $7/month
- **Web Services**: 750 hours/month free (enough for 1 service always-on)
- **Bandwidth**: 100GB/month free

### After Free Tier
- **Database**: $7/month (Starter)
- **Backend**: $7/month (Starter, 0.5GB RAM)
- **Frontend**: $7/month (Starter, 0.5GB RAM)
- **Total**: ~$21/month for all services

### Cost Optimization Tips
1. **Use one web service**: Combine frontend + backend in a single service
2. **Use Haiku model**: Cheaper API costs than Sonnet
3. **Set up caching**: Cache common queries
4. **Monitor usage**: Check Render dashboard regularly

## 🔄 Continuous Deployment

Render automatically redeploys when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature"
git push origin main

# Render will automatically:
# 1. Pull latest code
# 2. Rebuild services
# 3. Deploy (~5-10 mins)
```

## 📊 Monitoring

### Logs
- View real-time logs in Render dashboard
- Filter by service
- Download logs for debugging

### Metrics
- CPU usage
- Memory usage
- Request count
- Response times

### Alerts (Paid plans)
- Email notifications
- Slack integration
- Custom webhooks

## 🆘 Support

**Render Documentation**: https://render.com/docs
**Render Community**: https://community.render.com
**Anthropic API Docs**: https://docs.anthropic.com

## 🎉 Next Steps

After successful deployment:

1. **Set up monitoring**: Enable error tracking
2. **Add analytics**: Track usage patterns
3. **Implement caching**: Reduce API costs
4. **Add rate limiting**: Prevent abuse
5. **Custom domain**: Make it official!

---

**Deployed by**: Adyai Team
**Last Updated**: 2025-01-02
