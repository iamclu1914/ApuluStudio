# Credential Rotation Guide

This document provides instructions for rotating all credentials and API keys used by Apulu Suite. Rotate credentials immediately if you suspect any unauthorized access, and periodically as part of security best practices.

## Emergency Rotation Checklist

If credentials have been exposed (e.g., committed to public repository):

1. [ ] Rotate ALL credentials listed below immediately
2. [ ] Review access logs for unauthorized activity
3. [ ] Revoke any suspicious sessions/tokens
4. [ ] Update production environment variables
5. [ ] Restart all services
6. [ ] Monitor for suspicious activity for 48-72 hours

---

## Supabase Credentials

### Database Password

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Navigate to **Project Settings** > **Database**
4. Click **Reset database password**
5. Copy the new password
6. Update `DATABASE_URL` in your `.env` file:
   ```
   DATABASE_URL=postgresql+asyncpg://postgres.[project-ref]:[NEW_PASSWORD]@aws-0-[region].pooler.supabase.com:6543/postgres
   ```
7. Restart backend services

### API Keys (Anon Key & Service Role Key)

**Note**: Rotating Supabase API keys requires creating a new project. For most security incidents, rotating the database password is sufficient.

If you must rotate API keys:

1. Create a new Supabase project
2. Migrate your database schema and data
3. Update all environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_KEY`
4. Update frontend environment variables:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
5. Deploy changes to all environments

**Alternative** (if available in your Supabase plan):
- Check **Project Settings** > **API** for key regeneration options

---

## OpenAI API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Click **Create new secret key**
3. Name it (e.g., "Apulu Suite Production")
4. Copy the key immediately (it won't be shown again)
5. Delete the old compromised key
6. Update `OPENAI_API_KEY` in your `.env` file
7. Restart backend services

**Best Practices**:
- Set usage limits at **Settings** > **Limits**
- Enable budget alerts
- Use separate keys for development and production

---

## Anthropic API Key

1. Go to [Anthropic Console](https://console.anthropic.com/settings/keys)
2. Click **Create Key**
3. Name it appropriately
4. Copy the key
5. Disable or delete the old key
6. Update `ANTHROPIC_API_KEY` in your `.env` file
7. Restart backend services

---

## Meta (Facebook/Instagram/Threads) Credentials

### App Secret

1. Go to [Meta for Developers](https://developers.facebook.com/apps/)
2. Select your app
3. Navigate to **Settings** > **Basic**
4. Click **Show** next to App Secret, then **Reset**
5. Confirm the reset
6. Copy the new secret
7. Update `META_APP_SECRET` in your `.env` file
8. Restart backend services

**Warning**: Resetting the app secret will invalidate all existing access tokens.

### Access Token (Long-Lived)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app
3. Click **Generate Access Token**
4. Select required permissions:
   - `pages_manage_posts`
   - `pages_read_engagement`
   - `instagram_basic`
   - `instagram_content_publish`
   - `instagram_manage_insights`
5. Exchange for long-lived token:
   ```
   GET /oauth/access_token?
     grant_type=fb_exchange_token&
     client_id={app-id}&
     client_secret={app-secret}&
     fb_exchange_token={short-lived-token}
   ```
6. Update `META_ACCESS_TOKEN` in your `.env` file
7. Restart backend services

**Note**: Long-lived tokens expire after ~60 days. Set up a refresh mechanism or calendar reminder.

---

## Bluesky Credentials

### App Password

1. Log in to [Bluesky](https://bsky.app/)
2. Go to **Settings** > **App Passwords**
3. Click **Add App Password**
4. Name it (e.g., "Apulu Suite")
5. Copy the generated password
6. Delete the old app password
7. Update `BLUESKY_APP_PASSWORD` in your `.env` file
8. Restart backend services

**Security Notes**:
- App passwords have full account access
- Each app should have its own password
- Never use your main account password

---

## LATE API Key

1. Log in to [LATE Dashboard](https://getlate.dev)
2. Navigate to **API Keys** or **Settings**
3. Generate a new API key
4. Revoke the old key
5. Update `LATE_API_KEY` in your `.env` file
6. Restart backend services

---

## LinkedIn Credentials

### Client Secret

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Select your application
3. Navigate to **Auth** tab
4. Click **Reset** or **Regenerate** for Client Secret
5. Copy the new secret
6. Update `LINKEDIN_CLIENT_SECRET` in your `.env` file
7. Restart backend services

**Note**: Resetting the client secret will invalidate all existing OAuth tokens. Users will need to re-authorize.

### OAuth Tokens

LinkedIn OAuth tokens expire and need periodic refresh:
- Access tokens: 60 days
- Refresh tokens: 365 days

Implement automatic token refresh in your application.

---

## X (Twitter) Credentials

### API Keys and Secrets

1. Go to [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)
2. Select your project/app
3. Navigate to **Keys and Tokens**
4. Click **Regenerate** for:
   - API Key and Secret
   - Access Token and Secret
5. Copy all new values
6. Update in your `.env` file:
   ```
   X_API_KEY=new-api-key
   X_API_SECRET=new-api-secret
   X_ACCESS_TOKEN=new-access-token
   X_ACCESS_SECRET=new-access-secret
   ```
7. Restart backend services

**Note**: Regenerating keys invalidates all existing tokens.

---

## Application Secret Key

The `SECRET_KEY` is used for signing tokens and sessions.

### Generate New Key

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Using OpenSSL
openssl rand -base64 32
```

### Rotation Steps

1. Generate a new secret key
2. Update `SECRET_KEY` in your `.env` file
3. Restart backend services
4. Note: All existing sessions will be invalidated

---

## Environment Update Procedure

After rotating any credentials:

### Local Development

1. Update your local `.env` file
2. Restart Docker containers:
   ```bash
   docker-compose down
   docker-compose up -d
   ```
   Or restart the backend manually:
   ```bash
   # In backend directory
   uvicorn app.main:app --reload
   ```

### Production Deployment

1. Update environment variables in your hosting platform:
   - **Vercel**: Project Settings > Environment Variables
   - **Railway**: Project > Variables
   - **AWS**: Parameter Store / Secrets Manager
   - **Heroku**: Config Vars
   - **Docker**: Update docker-compose.prod.yml or secrets

2. Trigger a new deployment or restart services

3. Verify the application is working correctly

4. Monitor logs for authentication errors

---

## Rotation Schedule Recommendations

| Credential | Rotation Frequency | Priority |
|------------|-------------------|----------|
| SECRET_KEY | Annually or on suspicion | High |
| Database Password | Quarterly | High |
| API Keys (AI providers) | Annually | Medium |
| Meta Access Token | Every 60 days (expires) | High |
| OAuth Client Secrets | Annually | Medium |
| Bluesky App Password | Annually | Low |
| LATE API Key | Annually | Low |

---

## Monitoring and Alerts

After credential rotation, monitor for:

1. **Authentication Errors**: Check backend logs for 401/403 errors
2. **API Rate Limits**: Some providers reset limits with new keys
3. **Third-party Integrations**: Verify all platform connections work
4. **User Sessions**: Users may need to re-authenticate

### Log Monitoring Commands

```bash
# Docker logs
docker-compose logs -f backend

# Search for auth errors
docker-compose logs backend | grep -i "auth\|401\|403\|unauthorized"
```

---

## Security Best Practices

1. **Never commit credentials** to version control
2. **Use different credentials** for development, staging, and production
3. **Implement least privilege** - only request permissions you need
4. **Set up billing alerts** for paid API services
5. **Enable 2FA** on all developer accounts
6. **Review access logs** regularly
7. **Use secrets management** tools in production (AWS Secrets Manager, HashiCorp Vault, etc.)
8. **Document all rotations** with date and reason

---

## Emergency Contacts

If you discover a security incident:

1. Immediately rotate all potentially compromised credentials
2. Review this document for rotation procedures
3. Check platform-specific security dashboards for suspicious activity
4. Consider engaging professional security assistance for serious breaches
