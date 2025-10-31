# OAuth Google & Microsoft Identity Setup Guide
## Contractor Portal - Complete Implementation

---

## 🎯 **WHAT WAS IMPLEMENTED**

### 1. **OAuth Login Flow** (Google & Microsoft)
- Users can click "Continue with Google" or "Continue with Microsoft" on login page
- OAuth providers redirect back with user identity
- New users are automatically created in "pending" status
- Existing users get their role from the database

### 2. **Pending Approval System**
- New OAuth signups create users with `status = 'pending'`
- Pending users are redirected to `/static/pending-approval.html`
- Admins can approve pending users and assign roles (Admin, Manager, User)
- Admins can reject/delete pending users
- Admins can suspend/reactivate users

### 3. **Database Schema**
- Added `identities` table to track OAuth provider accounts
- Enhanced `users` table with:
  - `display_name` (from OAuth profile)
  - `avatar_url` (from OAuth profile picture)
  - `status` (pending/active/suspended)
  - `last_login_at`
  - `created_at` and `updated_at` timestamps

### 4. **Admin Interface**
- New page: `/static/ApprovePendingUsers.html`
- Shows all pending OAuth signups
- Admins can approve with role assignment
- Admins can reject signups
- Visual cards showing user info, email, OAuth providers, and signup time

---

## 📋 **SETUP CHECKLIST**

### **Step 1: Install Dependencies**
```bash
cd contractor-portal-main
pip install -r requirements.txt --break-system-packages
```

New dependencies added:
- `authlib` - OAuth client library
- `itsdangerous` - Session management

### **Step 2: Run Database Migration**
```bash
mysql -u contractor -p contractor_db < migrations/2025-10-31_oauth_identities.sql
```

This will:
- Add OAuth columns to `users` table
- Create `identities` table
- Add indexes for performance
- Set existing users to 'active' status

### **Step 3: Configure OAuth Providers**

#### **Google OAuth Setup**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable "Google+ API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set Authorized redirect URIs:
   - `http://localhost:8080/auth/google/callback` (for local)
   - `https://your-domain.com/auth/google/callback` (for production)
6. Copy Client ID and Client Secret

#### **Microsoft OAuth Setup**
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to "Azure Active Directory" → "App registrations"
3. Click "New registration"
4. Set redirect URIs:
   - `http://localhost:8080/auth/microsoft/callback` (for local)
   - `https://your-domain.com/auth/microsoft/callback` (for production)
5. Go to "Certificates & secrets" → Create new client secret
6. Copy Application (client) ID and Client Secret

### **Step 4: Set Environment Variables**

Create a `.env` file in your project root:

```env
# App Settings
APP_BASE_URL=http://localhost:8080
APP_JWT_SECRET=your-super-secret-jwt-key-change-this
APP_JWT_EXP_MIN=120

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth
MS_TENANT=common
MS_CLIENT_ID=your-microsoft-client-id
MS_CLIENT_SECRET=your-microsoft-client-secret

# Database (if needed)
DB_HOST=localhost
DB_USER=contractor
DB_PASSWORD=your-db-password
DB_NAME=contractor_db
```

**Important Notes:**
- `APP_BASE_URL` must match your actual domain (no trailing slash)
- `MS_TENANT=common` allows any Microsoft account. Use your tenant ID to restrict to your organization only.
- Change `APP_JWT_SECRET` to a strong random string

### **Step 5: Test the OAuth Flow**

1. **Start the application:**
   ```bash
   python main.py
   ```

2. **Test Google Login:**
   - Go to `http://localhost:8080/login.html`
   - Click "Continue with Google"
   - Sign in with a Google account
   - Should redirect to "Pending Approval" page

3. **Test Microsoft Login:**
   - Click "Continue with Microsoft"
   - Sign in with Microsoft account
   - Should redirect to "Pending Approval" page

4. **Approve New User (as Admin):**
   - Login as an existing admin (with password)
   - Go to `http://localhost:8080/static/ApprovePendingUsers.html`
   - Select role for new user
   - Click "✓ Approve"

5. **Test Approved User Login:**
   - Logout
   - Click "Continue with Google/Microsoft" again
   - Should now redirect to proper dashboard based on assigned role

---

## 🗂️ **FILES MODIFIED/CREATED**

### **New Files:**
- `migrations/2025-10-31_oauth_identities.sql` - Database schema
- `static/pending-approval.html` - Pending user page
- `static/ApprovePendingUsers.html` - Admin approval interface
- `OAUTH_SETUP_GUIDE.md` - This file

### **Modified Files:**
- `routers/auth_oidc.py` - Updated to check user status before issuing token
- `db/identities.py` - Enhanced with status/role checks
- `routes/auth_routes.py` - Added admin approval endpoints
- `requirements.txt` - Added authlib and itsdangerous

### **Unchanged (Already Working):**
- `static/login.html` - Already has OAuth buttons
- `config/auth_settings.py` - Already configured for OAuth

---

## 🔧 **API ENDPOINTS ADDED**

| Endpoint | Method | Access | Purpose |
|----------|--------|--------|---------|
| `/admin/pending-users/` | GET | Admin | List all pending OAuth signups |
| `/admin/approve-user/{user_id}` | POST | Admin | Approve user and assign role |
| `/admin/reject-user/{user_id}` | POST | Admin | Reject and delete pending user |
| `/admin/suspend-user/{user_id}` | POST | Admin | Suspend an active user |
| `/admin/reactivate-user/{user_id}` | POST | Admin | Reactivate suspended user |

---

## 🧪 **TESTING SCENARIOS**

### **Scenario 1: New User Signup**
1. User clicks "Continue with Google"
2. Completes Google authentication
3. System creates user with status='pending'
4. User sees "Pending Approval" page
5. Admin approves user as "User" role
6. User can now login and access User Dashboard

### **Scenario 2: Existing Email with OAuth**
1. User has password-based account with email user@example.com
2. User clicks "Continue with Google" using same email
3. System links Google identity to existing account
4. User can now login with either password OR Google

### **Scenario 3: Role-Based Redirect**
1. Admin approves user as "Manager"
2. User logs in with OAuth
3. System reads role from database
4. User redirected to Manager Dashboard

### **Scenario 4: Suspended User**
1. Admin suspends user
2. User tries to login with OAuth
3. Gets 403 error: "Your account has been suspended"

---

## ⚠️ **KNOWN ISSUES & NEXT STEPS**

### **Current Limitations:**
1. **No email notifications** - Users don't get notified when approved
2. **No user-initiated role request** - Users can't request specific roles during signup
3. **Password field still required in users table** - OAuth users don't need passwords

### **Recommended Improvements:**
1. **Add Email Notifications:**
   - Send welcome email when user is approved
   - Notify admins when new users signup
   
2. **Password Optional:**
   - Make password field nullable in users table
   - Update password-based login to handle OAuth-only users

3. **Role Request During Signup:**
   - Add a signup page where users can indicate if they're contractors or managers
   - Store this preference for admin review

4. **Admin Dashboard Widget:**
   - Show pending approval count on Admin Dashboard
   - Link directly to ApprovePendingUsers page

5. **Audit Log:**
   - Track who approved/rejected users and when
   - Store suspension reasons

---

## 🚀 **DEPLOYMENT NOTES**

### **For Cloud Run / VPS:**
1. Update `APP_BASE_URL` in environment variables to your production URL
2. Update OAuth redirect URIs in Google/Microsoft consoles
3. Ensure database migration has run on production DB
4. Test OAuth flow on production before announcing

### **Security Considerations:**
- Keep `APP_JWT_SECRET` secure and unique per environment
- Use HTTPS in production (OAuth requires it)
- Consider rate limiting on OAuth endpoints
- Store secrets in environment variables, never in code

---

## 📞 **SUPPORT**

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check server logs for Python errors
3. Verify environment variables are set correctly
4. Ensure database migration ran successfully
5. Test with both Google and Microsoft to isolate provider-specific issues

Common errors:
- "OIDC authorization failed" → Check client ID/secret
- "Redirect URI mismatch" → Update OAuth console settings
- "Database connection error" → Check MySQL credentials
- "401 Unauthorized" → Check JWT secret configuration

---

## ✅ **SUCCESS CRITERIA**

You'll know OAuth is working when:
- ✓ New users can signup with Google/Microsoft
- ✓ New users see "Pending Approval" page
- ✓ Admins can see pending users
- ✓ Admins can approve and assign roles
- ✓ Approved users can login and access correct dashboard
- ✓ Existing users can link OAuth identities to accounts
- ✓ Admins can suspend/reactivate users

---

**Implementation Complete! 🎉**

All OAuth functionality has been implemented. Follow the setup checklist above to get it running.
