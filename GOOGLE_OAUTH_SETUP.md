# Google OAuth Setup Guide

## Overview
This guide walks you through setting up Google OAuth authentication for the Contractor Portal, allowing users to sign in with their Google accounts.

---

## Step 1: Create Google Cloud Project

### 1.1 Go to Google Cloud Console
1. Visit: https://console.cloud.google.com/
2. Sign in with your Google account
3. Click "Select a project" → "New Project"

### 1.2 Create New Project
- **Project Name**: `Contractor Portal` (or your preferred name)
- **Organization**: Leave default or select your organization
- Click **"Create"**

### 1.3 Enable Required APIs
1. Go to **APIs & Services** → **Library**
2. Search for and enable:
   - **Google+ API** (for basic profile info)
   - **People API** (for user details)

---

## Step 2: Configure OAuth Consent Screen

### 2.1 Navigate to Consent Screen
1. Go to **APIs & Services** → **OAuth consent screen**
2. Choose **External** (unless you have Google Workspace)
3. Click **"Create"**

### 2.2 Fill in App Information
**App Information:**
- **App name**: `Contractor Portal`
- **User support email**: Your email address
- **App logo**: (Optional) Upload your logo

**App domain:**
- **Application home page**: `https://snow-contractor.com`
- **Application privacy policy link**: `https://snow-contractor.com/privacy` (create this page)
- **Application terms of service link**: `https://snow-contractor.com/terms` (create this page)

**Authorized domains:**
- Add: `snow-contractor.com`

**Developer contact information:**
- Your email address

### 2.3 Scopes
Click **"Add or Remove Scopes"** and select:
- `userinfo.email` - See your primary Google Account email address
- `userinfo.profile` - See your personal info
- `openid` - Authenticate using OpenID Connect

### 2.4 Test Users (if External)
Add test email addresses that can access during development:
- Your email
- Team member emails

### 2.5 Summary
Review and click **"Back to Dashboard"**

---

## Step 3: Create OAuth 2.0 Credentials

### 3.1 Create Credentials
1. Go to **APIs & Services** → **Credentials**
2. Click **"+ Create Credentials"**
3. Select **"OAuth client ID"**

### 3.2 Configure OAuth Client
**Application type**: Web application

**Name**: `Contractor Portal Web Client`

**Authorized JavaScript origins:**
```
http://localhost:8000
https://snow-contractor.com
```

**Authorized redirect URIs:**
```
http://localhost:8000/auth/google/callback
https://snow-contractor.com/auth/google/callback
```

### 3.3 Save Credentials
1. Click **"Create"**
2. **Copy the Client ID** - You'll need this
3. **Copy the Client Secret** - You'll need this
4. Click **"OK"**

---

## Step 4: Update Environment Variables

### 4.1 Local Development (.env)
Add to `r:\Contractor App\app\.env`:

```env
# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

### 4.2 Production (VPS)
SSH into your VPS and update the systemd service:

```bash
sudo nano /etc/systemd/system/contractor-portal.service
```

Add these environment variables:
```ini
Environment="GOOGLE_CLIENT_ID=410182375480-j0fblvtts5j97qrm2eor6suck2d4cu4m.apps.googleusercontent.com"
Environment="GOOGLE_CLIENT_SECRET=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"
Environment="GOOGLE_REDIRECT_URI=https://snow-contractor.com/auth/google/callback"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart contractor-portal
```

---

## Step 5: Install Required Python Packages

### 5.1 Add to requirements.txt
```bash
cd "r:\Contractor App\app"
echo "authlib" >> requirements.txt
echo "httpx" >> requirements.txt
```

### 5.2 Install Packages
```bash
pip install authlib httpx
```

---

## Step 6: Backend Implementation (Already Done)

The backend OAuth routes are already implemented in `app/routers/auth_oidc.py`:

**Key endpoints:**
- `GET /auth/google/login` - Initiates Google OAuth flow
- `GET /auth/google/callback` - Handles OAuth callback
- `POST /auth/google/link` - Links Google account to existing user

**Features:**
- Creates user account on first login (pending approval)
- Links Google identity to existing users
- Stores identity information in `identities` table
- Generates JWT token for authenticated sessions

---

## Step 7: Frontend Implementation

### 7.1 Login Page Updates
The login page (`static/login.html`) needs a "Sign in with Google" button:

```html
<button onclick="loginWithGoogle()" class="google-signin-btn">
    <img src="/static/google-icon.svg" alt="Google" width="20" height="20">
    Sign in with Google
</button>
```

```javascript
function loginWithGoogle() {
    window.location.href = '/auth/google/login';
}
```

### 7.2 Callback Handling
After Google authentication, users are redirected to `/static/auth-callback.html` which:
1. Extracts the JWT token from URL
2. Stores it in localStorage
3. Redirects to appropriate dashboard based on role

---

## Step 8: Database Tables (Already Created)

Required tables are already defined:

**users table:**
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    avatar_url VARCHAR(500),
    role ENUM('Admin', 'Manager', 'Contractor', 'Subcontractor', 'User'),
    status ENUM('active', 'pending', 'suspended'),
    ...
);
```

**identities table:**
```sql
CREATE TABLE identities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY (provider, provider_user_id)
);
```

---

## Step 9: Testing the OAuth Flow

### 9.1 Local Testing
1. Start your local server:
   ```bash
   cd "r:\Contractor App\app"
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. Navigate to: http://localhost:8000/static/login.html

3. Click "Sign in with Google"

4. Complete Google OAuth flow

5. Check if redirected to dashboard

### 9.2 Test Scenarios
- ✅ First-time user (should create pending account)
- ✅ Existing user with same email
- ✅ Multiple Google accounts
- ✅ Linking Google to existing password account

### 9.3 Verify Database
Check that records are created:
```sql
-- Check new user
SELECT * FROM users WHERE email = 'test@gmail.com';

-- Check identity link
SELECT * FROM identities WHERE provider = 'google';
```

---

## Step 10: Production Deployment

### 10.1 Update DNS (if needed)
Ensure `snow-contractor.com` points to your VPS IP: `72.61.0.186`

### 10.2 SSL Certificate
Google OAuth requires HTTPS in production. Ensure Let's Encrypt SSL is active:
```bash
sudo certbot renew --dry-run
```

### 10.3 Deploy Backend
Copy updated files to VPS:
```bash
scp app/routers/auth_oidc.py root@72.61.0.186:/opt/contractor-portal/routers/
scp app/static/login.html root@72.61.0.186:/opt/contractor-portal/static/
```

### 10.4 Restart Service
```bash
ssh root@72.61.0.186 "systemctl restart contractor-portal"
```

### 10.5 Test Production
1. Visit: https://snow-contractor.com/static/login.html
2. Click "Sign in with Google"
3. Complete OAuth flow
4. Verify login successful

---

## Security Best Practices

### ✅ DO:
- Use HTTPS in production (required by Google)
- Store client secret in environment variables (never in code)
- Validate state parameter to prevent CSRF
- Verify JWT tokens on every request
- Set appropriate token expiration times
- Use secure, httpOnly cookies if possible

### ❌ DON'T:
- Commit credentials to Git
- Share client secrets publicly
- Use HTTP in production
- Store tokens in URL parameters
- Skip email verification
- Allow unlimited login attempts

---

## Troubleshooting

### Error: "redirect_uri_mismatch"
**Cause**: The redirect URI doesn't match what's configured in Google Console

**Fix**:
1. Check Google Console → Credentials → Your OAuth Client
2. Ensure exact match: `https://snow-contractor.com/auth/google/callback`
3. No trailing slashes
4. Correct protocol (http vs https)

### Error: "invalid_client"
**Cause**: Client ID or Secret is incorrect

**Fix**:
1. Verify environment variables are set correctly
2. Check for extra spaces or quotes
3. Regenerate credentials if needed

### Error: "access_denied"
**Cause**: User declined authorization or not in test users

**Fix**:
1. Add user to test users in OAuth consent screen
2. Request app verification from Google (for production)

### Users Stuck in "Pending" Status
**Cause**: Admin approval workflow is enabled

**Fix**:
1. Log in as Admin
2. Navigate to "Approve Pending Users"
3. Approve the user and assign role

### Token Expired
**Cause**: JWT token has expired (default 24 hours)

**Fix**:
- User needs to log in again
- Consider implementing refresh tokens for longer sessions

---

## User Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User clicks "Sign in with Google"                       │
│    → Browser redirects to /auth/google/login               │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 2. Backend generates authorization URL                      │
│    → Redirects browser to Google OAuth consent screen       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 3. User authorizes app on Google                            │
│    → Google redirects to /auth/google/callback?code=...     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 4. Backend exchanges code for access token                  │
│    → Fetches user profile from Google                       │
│    → Creates/updates user in database                       │
│    → Generates JWT token                                    │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│ 5. Redirect to frontend with JWT token                      │
│    → Frontend stores token in localStorage                  │
│    → Redirects to appropriate dashboard                     │
└─────────────────────────────────────────────────────────────┘
```

---

## Admin Approval Workflow

When a new user signs in with Google:

1. **User record created** with `status = 'pending'`
2. **Admin notification** (optional - can add email notification)
3. **User sees "Pending Approval" page**
4. **Admin logs in** and goes to "Approve Pending Users"
5. **Admin assigns role** (Admin, Manager, Contractor, User)
6. **User status** changes to `'active'`
7. **User can now access** the portal on next login

---

## Testing Checklist

### Before Production:
- [ ] Client ID and Secret configured
- [ ] Redirect URIs match exactly
- [ ] SSL certificate active
- [ ] Environment variables set on VPS
- [ ] Database tables created
- [ ] Test user can sign in
- [ ] Admin can approve users
- [ ] Tokens are validated correctly
- [ ] Error handling works
- [ ] Mobile responsive

### Production Launch:
- [ ] Remove test users (or keep for QA)
- [ ] Monitor error logs
- [ ] Set up user onboarding emails
- [ ] Document user instructions
- [ ] Plan for OAuth verification with Google

---

## Next Steps

### Immediate:
1. Get Google Client ID and Secret
2. Update environment variables
3. Test OAuth flow locally
4. Deploy to production

### Future Enhancements:
1. **Add Microsoft OAuth** (Azure AD) for enterprise customers
2. **Email Notifications** when new users sign up
3. **Profile Management** page where users can link/unlink accounts
4. **Two-Factor Authentication** (2FA) for enhanced security
5. **Session Management** dashboard showing active sessions
6. **Refresh Tokens** for longer session durations

---

## Support Resources

- **Google OAuth Documentation**: https://developers.google.com/identity/protocols/oauth2
- **Authlib Documentation**: https://docs.authlib.org/
- **OAuth 2.0 RFC**: https://tools.ietf.org/html/rfc6749
- **OpenID Connect**: https://openid.net/connect/

---

## Questions?

Common setup questions:

**Q: How long does verification take?**
A: For testing, instant. For production (>100 users), 1-3 weeks Google review.

**Q: Do I need a business account?**
A: No, personal Google account works fine.

**Q: What if users already have password accounts?**
A: They can link their Google account to existing account using the "Link Account" feature.

**Q: Can users have multiple OAuth providers?**
A: Yes! The `identities` table supports multiple providers per user.

**Q: What happens if email doesn't match?**
A: System creates a new user account. Admins can merge accounts manually if needed.
