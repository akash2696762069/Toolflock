# SMTP Titan Mail Setup Guide

## Step 1: Create .env File

Create a `.env` file in your project root directory with the following configuration:

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=toolflock

# SMTP Titan Mail Configuration
MAIL_SERVER=smtp.titan.email
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@yourdomain.com
MAIL_PASSWORD=your-titan-mail-password
MAIL_DEFAULT_SENDER=your-email@yourdomain.com

# Optional: Additional Security
MAIL_USE_SSL=False
MAIL_MAX_EMAILS=None
MAIL_ASCII_ATTACHMENTS=False
```

## Step 2: Get Titan Mail Credentials

1. **Sign up for Titan Mail** at [titan.email](https://titan.email)
2. **Create a new email account** for your domain
3. **Get your SMTP credentials**:
   - Username: your-email@yourdomain.com
   - Password: your-titan-mail-password
   - SMTP Server: smtp.titan.email
   - Port: 587 (TLS) or 465 (SSL)

## Step 3: Update .env File

Replace the placeholder values in your `.env` file:

```env
MAIL_USERNAME=admin@yourdomain.com
MAIL_PASSWORD=your-actual-titan-password
MAIL_DEFAULT_SENDER=admin@yourdomain.com
```

## Step 4: Test Email Configuration

1. **Start your Flask application**
2. **Try to sign up** with a new account
3. **Check your email** for verification link
4. **Verify the account** by clicking the link

## Step 5: Troubleshooting

### Common Issues:

1. **Authentication Failed**
   - Check your username and password
   - Ensure you're using the correct SMTP server

2. **Connection Timeout**
   - Check your firewall settings
   - Verify the SMTP port (587 or 465)

3. **TLS/SSL Issues**
   - Use port 587 for TLS
   - Use port 465 for SSL
   - Set `MAIL_USE_TLS=True` for port 587

### Test Connection:

```python
# Add this to your app.py temporarily for testing
@app.route('/test-email')
def test_email():
    try:
        msg = Message(
            'Test Email',
            recipients=['test@example.com']
        )
        msg.body = 'This is a test email from Toolflock'
        mail.send(msg)
        return 'Email sent successfully!'
    except Exception as e:
        return f'Email failed: {str(e)}'
```

## Security Notes:

1. **Never commit your .env file** to version control
2. **Use strong passwords** for your email accounts
3. **Enable 2FA** on your Titan Mail account
4. **Regularly rotate** your email passwords

## Production Deployment:

1. **Set environment variables** on your hosting platform
2. **Use production-grade** secret keys
3. **Monitor email delivery** logs
4. **Set up email bounce handling**

## Support:

- **Titan Mail Support**: [support.titan.email](https://support.titan.email)
- **Flask-Mail Documentation**: [flask-mail.readthedocs.io](https://flask-mail.readthedocs.io)
- **SMTP Configuration Guide**: [flask-mail.readthedocs.io/en/latest/config.html](https://flask-mail.readthedocs.io/en/latest/config.html)
