# Africa's Talking SMS Integration Setup

This guide explains how to configure Africa's Talking SMS for your Real Estate Management System.

## What is Africa's Talking?

Africa's Talking is a communications API provider that offers SMS, voice, and airtime services across Africa. It's particularly well-suited for Kenyan and African markets.

## Prerequisites

1. **Africa's Talking Account**: Sign up at [https://account.africastalking.com/](https://account.africastalking.com/)
2. **API Credentials**: You'll need:
   - Username (your account username)
   - API Key (from your Africa's Talking dashboard)

## Configuration Steps

### 1. Get Your Africa's Talking Credentials

1. Log in to your Africa's Talking account
2. Go to the **API** section
3. Copy your **Username** and **API Key**
4. For sandbox testing, use the sandbox credentials provided

### 2. Update Your `.env` File

Edit `backend/.env` and add/update the following:

```bash
# Enable Africa's Talking SMS backend
SMS_BACKEND=africastalking

# Africa's Talking credentials
AT_USERNAME=sandbox  # or your actual username
AT_API_KEY=PASTE_YOUR_SANDBOX_API_KEY_HERE  # Replace with your actual API key
AT_ENVIRONMENT=sandbox  # Use 'production' when ready for live SMS
AT_SENDER_ID=  # Optional: Your sender ID (e.g., "PropNoxa")
```

### 3. Test the Integration

Use the provided test script to verify SMS delivery:

```bash
cd backend
python scripts/test_sms.py +254712345678 "Test message from PropNoxa"
```

Replace `+254712345678` with your actual phone number.

### 4. Switch from Console to Africa's Talking

Once you've verified the integration works:

1. Update `SMS_BACKEND=africastalking` in your `.env`
2. Restart your backend server
3. Test MFA SMS codes by logging in and requesting an SMS backup code

## Phone Number Format

The system automatically normalizes phone numbers:

- **Kenyan numbers**:
  - `0712345678` → `+254712345678`
  - `712345678` → `+254712345678`
  - `+254712345678` → `+254712345678` (already correct)

- **International numbers**:
  - Must start with `+` and country code
  - Example: `+14155552671` (US)

## Features

Once configured, Africa's Talking SMS will be used for:

1. **MFA Backup Codes**: When users can't access their authenticator app, they can request an SMS code
2. **High-Priority Alerts**: Security events and critical notifications
3. **Password Reset Codes**: One-time codes for password recovery

## Sandbox vs Production

### Sandbox (Testing)
- Endpoint: `https://api.sandbox.africastalking.com`
- Free to use for development
- Messages are not actually delivered to real phones
- Use for initial integration testing

### Production (Live)
- Endpoint: `https://api.africastalking.com`
- Requires actual Africa's Talking credits
- Real SMS delivery to phones
- Set `AT_ENVIRONMENT=production` when ready

## Cost Considerations

- Africa's Talking charges per SMS
- Rates vary by destination country
- Check current pricing at [https://www.africastalking.com/pricing](https://www.africastalking.com/pricing)
- Consider bulk SMS packages for high-volume usage

## Troubleshooting

### SMS Not Sending

1. Check backend logs for error messages
2. Verify credentials are correct in `.env`
3. Ensure phone number format is correct
4. Check if you have sufficient Africa's Talking credits (production)

### Authentication Errors

- Verify `AT_USERNAME` and `AT_API_KEY` are correct
- Ensure API key is not expired
- Check if your Africa's Talking account is active

### Rate Limiting

- Africa's Talking has rate limits per second
- The system respects these limits automatically
- For high-volume sending, consider queueing messages

## Security Notes

- **Never commit `.env` to version control**
- In production, use a secrets manager (AWS Secrets Manager, Azure Key Vault, etc.)
- Rotate API keys periodically
- Monitor SMS usage for unusual activity

## Switching Back to Console

If you need to disable SMS delivery (e.g., for testing):

```bash
SMS_BACKEND=console
```

This will log SMS messages to the console instead of sending them.

## Additional Resources

- [Africa's Talking SMS API Documentation](https://developers.africastalking.com/sms/send)
- [Africa's Talking Dashboard](https://account.africastalking.com/)
- [SMS Pricing](https://www.africastalking.com/pricing)

## Support

If you encounter issues:

1. Check the backend logs: `docker-compose logs api`
2. Review Africa's Talking dashboard for error messages
3. Test with the provided test script
4. Ensure your phone number is in the correct format
