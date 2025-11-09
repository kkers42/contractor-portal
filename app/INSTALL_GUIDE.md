# Contractor Portal - Installation Guide

## Quick Start

### Default Admin Credentials (Backdoor Access)

For initial installation, you can login with these default credentials **even if your database is empty**:

```
Email: admin@contractor.local
Password: ContractorAdmin2025!
```

**IMPORTANT SECURITY NOTES:**
- These credentials bypass the database and provide immediate Admin access
- They are configured in your `.env` file
- **CHANGE THESE IMMEDIATELY IN PRODUCTION**
- To disable backdoor access, remove or clear these environment variables:
  - `BACKDOOR_ADMIN_EMAIL`
  - `BACKDOOR_ADMIN_PASSWORD`

### Installation Steps

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment Variables**
   - Copy `.env.example` to `.env` (if exists)
   - Or edit `.env` directly
   - Set your database credentials
   - Configure OAuth providers (optional)

3. **Set Up Database**
   ```bash
   # Login to MySQL
   mysql -u root -p

   # Create database
   CREATE DATABASE contractor_portal;

   # Import schema (if you have a backup)
   mysql -u root -p contractor_portal < contractor_portal_backup.sql

   # Run OAuth migration
   mysql -u root -p contractor_portal < migrations/2025-10-31_oauth_identities.sql
   ```

4. **Start the Application**
   ```bash
   python main.py
   # Or using uvicorn directly:
   uvicorn main:app --host 0.0.0.0 --port 8080 --reload
   ```

5. **Access the Portal**
   - Open browser: `http://localhost:8080/static/login.html`
   - Login with backdoor credentials
   - Create your first real admin user
   - **Disable backdoor access**

### Post-Installation Security

After creating your first admin user, secure your installation:

1. **Update `.env` file:**
   ```env
   # Disable backdoor by removing or commenting out:
   # BACKDOOR_ADMIN_EMAIL=
   # BACKDOOR_ADMIN_PASSWORD=
   ```

2. **Change JWT Secret:**
   ```env
   APP_JWT_SECRET=<generate-a-secure-random-string-here>
   SECRET_KEY=<another-secure-random-string>
   ```

3. **Secure Database Password:**
   - Change the default database password
   - Update `DB_PASSWORD` in `.env`

4. **Add `.env` to `.gitignore`:**
   ```bash
   echo ".env" >> .gitignore
   ```

### OAuth Setup (Optional)

To enable Google/Microsoft Single Sign-On:

1. **Google OAuth:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create OAuth 2.0 credentials
   - Add redirect URI: `http://your-domain/auth/google/callback`
   - Add credentials to `.env`:
     ```env
     GOOGLE_CLIENT_ID=your_client_id
     GOOGLE_CLIENT_SECRET=your_client_secret
     ```

2. **Microsoft OAuth:**
   - Go to [Azure Portal](https://portal.azure.com)
   - Register an application
   - Add redirect URI: `http://your-domain/auth/microsoft/callback`
   - Add credentials to `.env`:
     ```env
     MS_CLIENT_ID=your_client_id
     MS_CLIENT_SECRET=your_client_secret
     MS_TENANT=common
     ```

See `OAUTH_SETUP_GUIDE.md` for detailed OAuth configuration instructions.

## Troubleshooting

### "Database connection error"
- Check MySQL is running: `systemctl status mysql`
- Verify database credentials in `.env`
- Ensure database exists: `SHOW DATABASES;`

### "Invalid credentials" with backdoor login
- Check `.env` has `BACKDOOR_ADMIN_EMAIL` and `BACKDOOR_ADMIN_PASSWORD`
- Restart the application to reload environment variables
- Verify you're entering credentials exactly as in `.env`

### OAuth not working
- Check OAuth credentials are in `.env`
- Verify redirect URIs match in OAuth provider console
- Check `APP_BASE_URL` is correct in `.env`
- Review application logs for error details

## Support

For issues or questions:
- Check `README.md` for project documentation
- Review `OAUTH_SETUP_GUIDE.md` for OAuth specifics
- Check application logs for detailed error messages
