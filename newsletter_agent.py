#!/usr/bin/env python3
"""
AI Newsletter Summarizer Agent
Fetches AI newsletters from Gmail, summarizes with Claude, archives to Google Sheets
"""
import os
import base64
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.exceptions import RefreshError
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from anthropic import Anthropic

# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.modify']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def authenticate_gmail():
    """Authenticate with Gmail API"""
    creds = None
    # Load token from pickle if exists
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for next time
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)

def get_newsletter_emails(service, days=1, max_results=50):
    """Fetch newsletter emails from last N days"""
    # Calculate date for query
    date_threshold = (datetime.utcnow() - timedelta(days=days)).strftime('%Y/%m/%d')
    # Query for emails with "newsletters" label or matching newsletter patterns
    query = f'label:ai-newsletter after:{date_threshold}'
    try:
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()
        messages = results.get('messages', [])
        return messages
    except HttpError as e:
        print(f"Error fetching emails: {e}")
        return []

def extract_email_content(service, message_id):
    """Extract subject, sender, and body from email"""
    try:
        message = service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')

        # Extract body
        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
        else:
            if 'body' in message['payload'] and 'data' in message['payload']['body']:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

        return {
            'id': message_id,
            'subject': subject,
            'sender': sender,
            'body': body[:2000]  # Limit to first 2000 chars for API efficiency
        }
    except HttpError as e:
        print(f"Error extracting email {message_id}: {e}")
        return None

def extract_links(text):
    """Extract URLs from text"""
    url_pattern = r'https?://[^\s\)>\]"\']+'
    urls = re.findall(url_pattern, text)
    return list(set(urls))  # Remove duplicates

def summarize_newsletters(emails):
    """Summarize newsletters using Claude API"""
    client = Anthropic(api_key=os.getenv('CLAUDE_API_KEY'))

    # Prepare newsletter content for summarization
    newsletter_text = "\n\n---\n\n".join([
        f"From: {email['sender']}\nSubject: {email['subject']}\n\n{email['body']}"
        for email in emails
    ])

    prompt = f"""You are an expert newsletter analyst. Summarize the following AI newsletters from the last 24 hours.

Extract and organize:
1. KEY NEWS ITEMS (3-5 main stories with 1-2 sentence summaries)
2. IMPORTANT ANNOUNCEMENTS (product launches, updates, major news)
3. INTERESTING INSIGHTS (unique perspectives or deep dives)
4. RELEVANT LINKS (extract all important URLs with their context)

Format output as:
## KEY NEWS
- [Story 1]: [Summary]
- [Story 2]: [Summary]

## ANNOUNCEMENTS
- [Announcement 1]
- [Announcement 2]

## INSIGHTS
- [Insight 1]
- [Insight 2]

## LINKS
- [URL]: [Context/Source]
- [URL]: [Context/Source]

NEWSLETTERS:
{newsletter_text}

Generate a professional, concise summary suitable for a busy executive."""

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        return message.content[0].text
    except Exception as e:
        print(f"Error summarizing with Claude: {e}")
        return None

def create_email_body(summary, emails):
    """Create HTML email body with summary and links"""
    # Extract all links from all emails
    all_links = []
    for email in emails:
        links = extract_links(email['body'])
        for link in links:
            all_links.append({
                'url': link,
                'from': email['sender']
            })

    # Remove duplicates while preserving order
    seen = set()
    unique_links = []
    for item in all_links:
        if item['url'] not in seen:
            seen.add(item['url'])
            unique_links.append(item)

    # Create HTML email
    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
    <h1>\U0001f4f0 AI Newsletter Digest</h1>
    <p><em>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}</em></p>
    <hr>
    <h2>Summary</h2>
    <div style="background-color: #f5f5f5; padding: 15px; border-left: 4px solid #007bff;">
        {summary.replace(chr(10), '<br>')}
    </div>
    <hr>
    <h2>Source Newsletters</h2>
    <ul>
"""
    # Add newsletter sources
    for email in emails:
        html_body += f"        <li><strong>{email['sender']}</strong><br><em>{email['subject']}</em></li>\n"

    html_body += """    </ul>
    <hr>
    <h2>Key Links</h2>
    <ul>
"""
    # Add extracted links
    for item in unique_links[:20]:  # Limit to 20 links
        html_body += f"        <li><a href='{item['url']}'>{item['url']}</a><br><small>From: {item['from']}</small></li>\n"

    html_body += """    </ul>
    <hr>
    <p style="color: #999; font-size: 12px;">
        This digest was automatically generated by your AI Newsletter Agent.
        <br>Archive this email or move it to your newsletter folder for later reference.
    </p>
</body>
</html>
"""
    return html_body

def send_email(service, to_email, subject, html_body):
    """Send email via Gmail API"""
    try:
        message = {
            'raw': base64.urlsafe_b64encode(
                f"""From: me
To: {to_email}
Subject: {subject}
MIME-Version: 1.0
Content-type: text/html; charset=utf-8

{html_body}""".encode()
            ).decode()
        }
        service.users().messages().send(userId='me', body=message).execute()
        print(f"\u2713 Email sent to {to_email}")
        return True
    except HttpError as e:
        print(f"Error sending email: {e}")
        return False

def archive_to_google_sheets(emails, summary):
    """Log to Google Sheets (optional - requires additional setup)"""
    archive_file = 'newsletter_archive.jsonl'
    timestamp = datetime.now().isoformat()
    archive_entry = {
        'timestamp': timestamp,
        'newsletter_count': len(emails),
        'senders': [e['sender'] for e in emails],
        'summary_preview': summary[:500],
        'links_count': sum(len(extract_links(e['body'])) for e in emails)
    }
    # Append to JSONL file
    with open(archive_file, 'a') as f:
        f.write(json.dumps(archive_entry) + '\n')
    print(f"\u2713 Archived to {archive_file}")

def main():
    """Main execution"""
    print("\U0001f916 Starting AI Newsletter Agent...")

    # Check for API key
    if not os.getenv('CLAUDE_API_KEY'):
        print("\u274c Error: CLAUDE_API_KEY environment variable not set")
        return

    # Authenticate with Gmail
    print("\U0001f510 Authenticating with Gmail...")
    try:
        service = authenticate_gmail()
    except RefreshError:
        print("\u274c Error: Gmail authentication failed. Token may have expired.")
        if os.path.exists(TOKEN_FILE):
            os.remove(TOKEN_FILE)
        return

    # Fetch newsletter emails
    print("\U0001f4e7 Fetching newsletters from last 24 hours...")
    emails = get_newsletter_emails(service, days=1)

    if not emails:
        print("\u2139\ufe0f No newsletters found in the last 24 hours")
        return

    print(f"\u2713 Found {len(emails)} newsletter(s)")

    # Extract email content
    print("\U0001f4dd Extracting email content...")
    email_contents = []
    for msg in emails:
        content = extract_email_content(service, msg['id'])
        if content:
            email_contents.append(content)

    if not email_contents:
        print("\u274c Error: Could not extract email contents")
        return

    # Summarize with Claude
    print("\U0001f9e0 Summarizing with Claude AI...")
    summary = summarize_newsletters(email_contents)

    if not summary:
        print("\u274c Error: Could not generate summary")
        return

    print("\u2713 Summary generated")

    # Create email body
    html_body = create_email_body(summary, email_contents)

    # Send email
    user_email = os.getenv('RECIPIENT_EMAIL', 'me')
    if user_email == 'me':
        try:
            profile = service.users().getProfile(userId='me').execute()
            user_email = profile['emailAddress']
        except Exception:
            user_email = 'your-email@gmail.com'

    print(f"\U0001f4e8 Sending summary email to {user_email}...")
    send_email(
        service,
        user_email,
        f"\U0001f4f0 AI Newsletter Digest - {datetime.now().strftime('%Y-%m-%d')}",
        html_body
    )

    # Archive
    archive_to_google_sheets(email_contents, summary)

    print("\n\u2705 Newsletter agent completed successfully!")

if __name__ == '__main__':
    main()
