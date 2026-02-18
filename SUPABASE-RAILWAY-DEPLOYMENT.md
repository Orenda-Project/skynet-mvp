# SkyNet Deployment Guide - Supabase + Railway

## Architecture Overview

**Database:** Supabase PostgreSQL (managed, with connection pooling)
**Hosting:** Railway (for FastAPI application)
**Benefits:** No Docker containers to manage, IPv4/IPv6 compatible, auto-scaling

---

## Prerequisites

✅ Supabase project created
✅ Railway account created
✅ GitHub repository with code

---

## Step 1: Supabase Setup (Already Complete!)

Your Supabase database is ready with:
- **Project URL:** https://tetwrjipyfsorwlvqvre.supabase.co
- **Database:** PostgreSQL with connection pooling enabled
- **Tables:** conversations, participants, syntheses (created via Alembic)

---

## Step 2: Deploy to Railway

### 2.1 Create New Railway Project

1. Go to https://railway.app/
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account and select the repository
5. Railway will automatically detect the project and start building

### 2.2 Configure Environment Variables

In Railway project settings → Variables, add:

```env
# Database - Supabase (use the pooler connection string)
DATABASE_URL=postgresql://postgres.tetwrjipyfsorwlvqvre:[YOUR-PASSWORD]@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres

# Supabase
SUPABASE_URL=https://tetwrjipyfsorwlvqvre.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_c94lP6qjqiYVbBknkJxdmA_Tw0rEUq3

# Application
APP_NAME=SkyNet
APP_VERSION=0.1.0
ENVIRONMENT=production
DEBUG=false

# OpenAI API
OPENAI_API_KEY=sk-proj-[YOUR-KEY]
OPENAI_MODEL_SYNTHESIS=gpt-4-turbo-preview
OPENAI_MODEL_EXTRACTION=gpt-4-mini
WHISPER_MODEL=whisper-1

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@skynet.ai
SMTP_FROM_NAME=SkyNet

# Security
SECRET_KEY=[generate-a-random-32-char-string]
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# CORS (update with your frontend URL)
CORS_ORIGINS=https://your-frontend.com,https://api.railway.app
```

### 2.3 Deploy

Railway will automatically:
1. Build the application using Nixpacks
2. Run `alembic upgrade head` to apply migrations
3. Start the FastAPI server with `uvicorn`
4. Assign a public URL (e.g., `https://skynet-production.up.railway.app`)

---

## Step 3: Verify Deployment

### 3.1 Check Health Endpoint

```bash
curl https://your-app.up.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "app": "SkyNet",
  "version": "0.1.0",
  "environment": "production"
}
```

### 3.2 Check API Documentation

Visit: `https://your-app.up.railway.app/docs`

You should see the FastAPI Swagger UI with all endpoints.

### 3.3 Check Database Tables

In Supabase Dashboard → Table Editor, verify:
- `conversations` table exists
- `participants` table exists
- `syntheses` table exists
- `alembic_version` table shows current migration

---

## Step 4: Test the Full Pipeline

### 4.1 Upload Audio File

```bash
curl -X POST https://your-app.up.railway.app/v1/transcription/upload \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Meeting",
    "description": "Testing SkyNet deployment",
    "participant_emails": ["test@example.com"]
  }'
```

### 4.2 Transcribe Audio

```bash
curl -X POST https://your-app.up.railway.app/v1/transcription/transcribe/{conversation_id} \
  -F "audio_file=@test_audio.mp3"
```

### 4.3 Generate Synthesis

```bash
curl -X POST https://your-app.up.railway.app/v1/synthesis/generate/{conversation_id}
```

### 4.4 Send Email

```bash
curl -X POST https://your-app.up.railway.app/v1/email/send/{conversation_id}
```

---

## Troubleshooting

### Database Connection Issues

**Problem:** Can't connect to Supabase
**Solution:**
- Verify `DATABASE_URL` uses the **pooler connection string** (not direct connection)
- Check that password special characters are URL-encoded (`$` = `%24`, `?` = `%3F`)
- Ensure connection pooling is enabled in Supabase project settings

### Migration Failures

**Problem:** Alembic migrations fail during deployment
**Solution:**
- Check Railway logs for specific error messages
- Verify Supabase database is accessible (not paused)
- Ensure `alembic_version` table doesn't have conflicts

### OpenAI API Errors

**Problem:** Synthesis generation fails
**Solution:**
- Verify `OPENAI_API_KEY` is set correctly in Railway variables
- Check OpenAI API usage limits: https://platform.openai.com/usage
- Ensure sufficient credits in OpenAI account

### Email Sending Issues

**Problem:** Emails not being sent
**Solution:**
- For Gmail: Use App Password (not regular password)
- Generate at: https://myaccount.google.com/apppasswords
- Alternative: Use SendGrid free tier (100 emails/day)

---

## Monitoring & Logs

### Railway Logs

View real-time logs in Railway dashboard:
```
Settings → Deployments → [Latest Deployment] → Logs
```

### Supabase Logs

View database logs in Supabase dashboard:
```
Logs → Postgres Logs
```

---

## Cost Estimates

### Supabase (Free Tier)
- Database: 500MB (free)
- Bandwidth: 2GB (free)
- Pooler connections: Included
- **Cost:** $0/month

### Railway (Free Tier)
- Compute: $5 credit/month (enough for MVP)
- After free tier: ~$10-20/month for basic usage
- **Cost:** $0-20/month

### OpenAI API
- Whisper: $0.006/minute
- GPT-4: ~$0.03-0.10/meeting
- **Estimated:** $15-30/month (for 10 meetings/day)

**Total Monthly Cost:** $15-50/month

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Test full pipeline end-to-end
3. ⏭️  Set up custom domain (optional)
4. ⏭️  Configure monitoring/alerts
5. ⏭️  Implement Phase 2 features (Neo4j knowledge graph)

---

## Support

- **Railway Docs:** https://docs.railway.app
- **Supabase Docs:** https://supabase.com/docs
- **FastAPI Docs:** https://fastapi.tiangolo.com
- **OpenAI API:** https://platform.openai.com/docs

---

**Last Updated:** February 18, 2026
**Status:** Ready for production deployment ✅
