# Render.com Deployment Guide for Samira Home Fashion Bot

This guide provides step-by-step instructions for deploying your Python Telegram bot to Render's free tier, ensuring it runs 24/7.

---

## Step 1: Prepare Your Project for Deployment

Before deploying, make sure your project is ready.

### 1. Finalize `requirements.txt`
Your `requirements.txt` file looks correct. No changes are needed.

### 2. Push Your Code to GitHub
Ensure all your latest code is on a GitHub repository.

```bash
# Add all your changes
git add .

# Commit the changes
git commit -m "Ready for Render deployment"

# Push to your main branch
git push origin main
```

---

## Step 2: Deploy on Render.com

1.  **Create an Account**: Go to dashboard.render.com and sign up using your GitHub account.

2.  **Create a New Web Service**:
    *   On your dashboard, click **New +** and select **Web Service**.
    *   Choose **Build and deploy from a Git repository** and connect the GitHub repository for your bot.

3.  **Configure the Service**:
    On the settings page, fill in the details exactly as follows:

    | Setting         | Value                                              |
    | --------------- | -------------------------------------------------- |
    | **Name**        | `samira-bot` (or any unique name)                  |
    | **Root Directory**| *Leave blank*                                      |
    | **Runtime**     | `Python 3`                                         |
    | **Build Command** | `pip install -r requirements.txt`                  |
    | **Start Command** | `uvicorn main:app --host 0.0.0.0 --port 10000`     |

    > **CRITICAL:** The **Start Command** (`uvicorn main:app ...`) must match your project structure.
    > *   `main`: Refers to the Python file `main.py`. If your file is `bot.py`, change this to `bot`.
    > *   `app`: Refers to the FastAPI instance, like `app = FastAPI()`. If you named it `my_app = FastAPI()`, change this to `my_app`.

---

## Step 3: Add Environment Variables

1.  After configuring the service, scroll down to the **Environment** section.
2.  Click **Add Environment Variable** and add the following keys and their corresponding values:

    | Key            | Value                                     | Description                               |
    | -------------- | ----------------------------------------- | ----------------------------------------- |
    | `BOT_TOKEN`    | `your_telegram_bot_token`                 | Get this from Telegram's @BotFather.      |
    | `ADMIN_IDS`    | `[123456789]`                             | Your Telegram User ID from @userinfobot.  |
    | `DATABASE_URL` | `sqlite+aiosqlite:///data/shop.db`        | **Important:** Use `/data/` for Render's persistent disk. |
    | `PYTHON_VERSION` | `3.11.9`                                  | Ensures Render uses a specific Python version. |

    > **Database Path on Render:** Render provides a persistent disk at `/data`. By setting the database path to `/data/shop.db`, your SQLite database **will persist** between restarts and deploys on the free tier.

3.  Click **Create Web Service** at the bottom of the page. Render will now start building and deploying your bot.

---

## Step 4: Keep the Bot Running 24/7

Render's free services "spin down" after 15 minutes of inactivity. To prevent this, use a free monitoring service.

1.  **Get Your Service URL**: On your Render dashboard, find the URL for your new service. It will look like `https://samira-bot.onrender.com`.

2.  **Set Up UptimeRobot**:
    *   Sign up for a free account at UptimeRobot.com.
    *   Click **+ Add New Monitor**.
    *   **Monitor Type**: `HTTP(s)`
    *   **Friendly Name**: `Samira Bot Monitor`
    *   **URL (or IP)**: Paste your Render service URL here.
    *   **Monitoring Interval**: Set to **5 minutes**.
    *   Click **Create Monitor**.

This will ping your bot every 5 minutes, keeping it awake and running continuously.

---

## Troubleshooting Common Errors

*   **Build Failed**:
    *   Go to the **Events** tab for your service on Render.
    *   Look at the build logs. The error is usually a typo in `requirements.txt` or a missing dependency.

*   **Deploy Failed / Application Error**:
    *   This is almost always an incorrect **Start Command**.
    *   **Error:** `Error loading ASGI app. Could not import module "main"` or `ModuleNotFoundError`.
    *   **Cause:** Your main Python file is not named `main.py`.
    *   **Fix:** Check your repository for the correct filename (e.g., `bot.py`, `app.py`). Go to **Settings** on Render and update the **Start Command**.
        *   If file is `bot.py`: `uvicorn bot:app --host 0.0.0.0 --port 10000`

*   **Bot is Not Responding**:
    *   Check the **Logs** tab on Render. Look for any runtime errors after "Bot started!".
    *   Verify that your `BOT_TOKEN` in the Environment Variables is correct.
    *   Make sure your UptimeRobot monitor is active and pointing to the correct `.onrender.com` URL.

*   **Database Issues**:
    *   Ensure your `DATABASE_URL` is set to `sqlite+aiosqlite:///data/shop.db` to use Render's free persistent disk. If you forget the `/data/` prefix, your database will be wiped on every deploy.
