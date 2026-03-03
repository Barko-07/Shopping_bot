# Railway Deployment Guide for Samira Home Fashion Bot

## Quick Deploy (One-Click)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/your-repo-link)

---

## Manual Deployment Steps

### Step 1: Push Code to GitHub

1. Create a new GitHub repository at https://github.com/new
2. Push your code (choose ONE option below):

**Option A - If remote has existing files (recommended):**
```
bash
git add .
git commit -m "Prepare for Railway deployment"
git pull origin main --allow-unrelated-histories
git push origin main
```

**Option B - Force push (WARNING: overwrites remote):**
```
bash
git add .
git commit -m "Prepare for Railway deployment"
git push -f origin main
```

**Option B - If starting fresh:**
```
bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

**Option C - If you want to change the remote:**
```
bash
git remote set-url origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### Step 2: Create Railway Account

1. Go to [Railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Verify your email

### Step 3: Create New Project

1. Click "New Project" → "Deploy from GitHub repo"
2. Select your repository
3. Wait for the build to complete

### Step 4: Configure Environment Variables

In Railway dashboard, go to **Variables** tab and add:

| Variable | Value | Description |
|----------|-------|-------------|
| `BOT_TOKEN` | `your_telegram_bot_token` | Get from @BotFather |
| `ADMIN_IDS` | `[123456789]` | Your Telegram user ID |
| `DATABASE_URL` | `sqlite+aiosqlite:///shop.db` | Keep default |
| `API_PORT` | `8000` | Keep default |
| `API_HOST` | `0.0.0.0` | Keep default |

**To get your Telegram User ID:**
- Message @userinfobot on Telegram
- It will show your ID

### Step 5: Deploy

1. Click "Deploy" button
2. Wait for deployment to complete (2-5 minutes)
3. Check logs for "Bot started!" message

---

## Important Notes

### Static Files (Images)
Railway's filesystem is ephemeral - uploaded images will be deleted on restart. 

**Solution:** Use external storage like:
- Cloudinary (recommended)
- AWS S3
- Or enable persistent disks on Railway (paid)

### Database
SQLite works on Railway but resets on each deployment. 

**For production, use PostgreSQL:**
1. In Railway: Add → Database → PostgreSQL
2. Get connection string from Variables
3. Update `DATABASE_URL` in your Railway variables

---

## After Deployment

1. **Telegram Bot**: Will start polling automatically
2. **API**: Available at `https://your-project-name.up.railway.app`
3. **API Docs**: `https://your-project-name.up.railway.app/docs`

---

## Troubleshooting

### Bot not responding?
- Check logs in Railway dashboard
- Ensure BOT_TOKEN is correct
- Verify ADMIN_IDS format: `[123456789]` (not "123456789")

### Deploy failed?
- Check the "Deploy" logs for errors
- Ensure all required packages are in requirements.txt

### Need to restart bot?
- In Railway: Click "Redeploy" button

---

## Keeping Bot Online (Free Tier)

Railway's free tier puts apps to sleep after 5 minutes of inactivity. 

**Workaround:** Use a free uptime monitor:
1. Sign up at [UptimeRobot.com](https://uptimerobot.com)
2. Add a monitor for your API URL
3. Set interval to every 5 minutes
4. This keeps your bot awake!

---

## Cost Estimate

| Service | Free Tier | Paid |
|---------|-----------|------|
| Railway | 500 hours/month | $5+/month |
| Telegram Bot | Free | Free |

For a personal bot, the free tier should work well!
