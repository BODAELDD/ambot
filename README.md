# Telegram Trading Bot

A Python bot that monitors Telegram channels for trading signals and forwards them to another channel.

## Features

- Monitors trading signals from specified Telegram channel
- Reformats and forwards signals to target channel
- Tracks win/loss sequences
- Sends webhook notifications for consecutive wins
- Environment variable configuration for security

## Free Hosting Options

### 1. Railway (Recommended)
1. Create account at [Railway.app](https://railway.app)
2. Connect your GitHub repository
3. Set environment variables in Railway dashboard
4. Deploy automatically

### 2. Render
1. Create account at [Render.com](https://render.com)
2. Connect your GitHub repository
3. Choose "Web Service" 
4. Set environment variables
5. Deploy

### 3. PythonAnywhere
1. Create free account at [PythonAnywhere.com](https://www.pythonanywhere.com)
2. Upload your files
3. Set up a "Always On" task (requires paid plan for 24/7)
4. Configure environment variables

### 4. Replit
1. Create account at [Replit.com](https://replit.com)
2. Import from GitHub
3. Set secrets (environment variables)
4. Keep alive with UptimeRobot

## Environment Variables

Set these environment variables in your hosting platform:

- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `STRING_SESSION`: Your Telegram session string
- `CHANNEL_USERNAME`: Source channel username (e.g., @PocketSignalsM1)
- `WEBHOOK_URL`: Webhook URL for notifications
- `BOT_TOKEN`: Your Telegram bot token
- `CHANNEL_ID`: Target channel ID (negative number)

## Local Development

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and fill in your values

3. Run the bot:
   ```bash
   python main.py
   ```

## Security Notes

- Never commit API keys or tokens to version control
- Use environment variables for all sensitive data
- Regularly rotate your API keys and tokens
- Consider using a dedicated Telegram account for the bot

## Deployment Steps

1. Push code to GitHub repository
2. Choose a hosting platform from the options above
3. Connect your repository
4. Set all required environment variables
5. Deploy and monitor logs

The bot will start automatically and begin monitoring the specified channel.