# 📰 AI Newsletter Agent

An automated agent that scans your Gmail inbox for AI newsletters, summarizes them using Claude AI, and delivers daily digests. **Completely free** using GitHub Actions.

## Features

✅ **Automated Daily Digests** - Runs on schedule, no manual intervention needed  
✅ **Claude AI Powered** - Uses Claude 3.5 Sonnet for intelligent summaries  
✅ **Gmail Integration** - Fetches emails labeled as newsletters  
✅ **Link Extraction** - Automatically extracts and organizes URLs from newsletters  
✅ **Email Delivery** - Sends formatted digests back to your inbox  
✅ **Archive** - Maintains a JSON log of all digests for future reference  
✅ **Zero Cost** - Runs on free GitHub Actions tier  
✅ **Open Source** - Full control over your data and automation  

## How It Works

```
Gmail (Newsletter Label)
    ↓
GitHub Actions (Daily 8 AM)
    ↓
Fetch & Process Emails
    ↓
Claude AI Summarization
    ↓
Link Extraction
    ↓
Email Digest Delivery
    ↓
JSON Archive
```

## Setup Guide

### Step 1: Set Up Gmail Labels

1. Go to Gmail
2. Create a label called `newsletters` (or any name you prefer)
3. Create filters to automatically label your AI newsletters:
   - Add filters for each newsletter sender
   - Apply label: `newsletters`

**Popular AI Newsletters to Subscribe To:**
- Hugging Face Digest
- OpenAI Newsletter
- Anthropic Updates
- TechCrunch AI
- The Batch (Andrew Ng)
- Import AI (Jack Clark)

### Step 2: Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project: `AI Newsletter Agent`
3. Enable Gmail API:
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Click "Create Credentials" → OAuth 2.0 Client ID
   - Application type: Desktop app
   - Download the JSON file
5. Run locally first to authenticate:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Place credentials.json in repo root
   cp ~/Downloads/client_secret_*.json credentials.json
   
   # Run locally
   export CLAUDE_API_KEY="your-claude-api-key"
   python newsletter_agent.py
   ```
   This creates `token.pickle` with your authenticated session

### Step 3: Encode Gmail Credentials for GitHub Secrets

1. After running locally, you have `credentials.json`
2. Encode it in base64:
   ```bash
   cat credentials.json | base64 -w 0
   ```
3. Copy the entire base64 output

### Step 4: Add GitHub Secrets

1. Go to your repository Settings → Secrets and variables → Actions
2. Add three secrets:

**CLAUDE_API_KEY**
- Your Anthropic API key from [console.anthropic.com](https://console.anthropic.com)
- You likely already have Claude Pro ($20/month), which includes API credits

**GMAIL_CREDENTIALS**
- The base64-encoded credentials from Step 3
- Make sure to include the entire base64 string

**RECIPIENT_EMAIL** (Optional)
- Email to receive digests
- If not set, sends to your Google account email
- Example: `your-email@gmail.com`

### Step 5: Test the Workflow

1. Go to Actions tab in your repo
2. Select "Daily AI Newsletter Digest"
3. Click "Run workflow" → "Run workflow"
4. Wait 30-60 seconds for it to complete
5. Check your email for the digest

### Step 6: Adjust Schedule (Optional)

Edit `.github/workflows/newsletter-agent.yml`:

```yaml
on:
  schedule:
    - cron: '0 8 * * *'  # 8 AM UTC daily
    # Change to your preferred time
    # Examples:
    # '0 7 * * *'  = 7 AM UTC
    # '0 9 * * *'  = 9 AM UTC
    # '*/6 * * * *' = Every 6 hours
```

## File Structure

```
ai-newsletter-agent/
├── newsletter_agent.py              # Main Python script
├── requirements.txt                 # Python dependencies
├── .github/workflows/
│   └── newsletter-agent.yml        # GitHub Actions workflow
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

## How to Customize

### Change the Gmail Label

Edit `newsletter_agent.py` line ~65:
```python
query = f'label:newsletters after:{date_threshold}'
# Change 'newsletters' to your label name
```

### Change Email Format

Modify the `create_email_body()` function in `newsletter_agent.py` to customize:
- HTML styling
- Section headers
- Summary format
- Link organization

### Add More Newsletter Sources

The script looks for any emails with the `newsletters` label. Just keep adding filters in Gmail!

## Troubleshooting

### "Token expired" Error

1. Delete `token.pickle` from repo
2. Run locally again: `python newsletter_agent.py`
3. Re-authenticate
4. Re-encode `credentials.json` to base64
5. Update GitHub secret

### Workflow Fails to Run

1. Check Actions tab for error logs
2. Verify all secrets are set correctly
3. Ensure credentials.json is valid (base64 encoded)
4. Try "Run workflow" manually to debug

### No Emails Found

1. Check Gmail has emails with `newsletters` label
2. Verify label name matches script
3. Check date range (script looks at last 24 hours)

### Not Receiving Digest Email

1. Check spam/promotions folder
2. Verify `RECIPIENT_EMAIL` secret is correct
3. Check Actions logs for send errors

## Cost Analysis

- **GitHub Actions**: Free (2,000 minutes/month, runs ~30 sec daily)
- **Gmail API**: Free
- **Claude API**: Pay-as-you-go ($0.003 per 1K input tokens)
  - Each daily digest = ~200-500 tokens = $0.0006-0.0015/day
  - **Monthly cost: $0.02-0.05** (essentially free)
  - With Claude Pro: Included in subscription

## License

MIT License - Feel free to fork, modify, and use!

## Support

If you encounter issues:

1. Check GitHub Actions logs
2. Review error messages in workflow output
3. Test locally with `python newsletter_agent.py`
4. Verify all secrets and credentials

## Future Enhancements

- [ ] Google Sheets integration for better archiving
- [ ] Topic-based email routing
- [ ] Slack notifications
- [ ] Custom summary length options
- [ ] Newsletter unsubscribe recommendations
- [ ] Reading time estimates

---

**Made with ❤️ for newsletter enthusiasts**
