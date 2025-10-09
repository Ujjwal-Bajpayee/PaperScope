# 🚀 PR Preview Deployments

This repository is configured with automated PR preview deployments. Every pull request automatically builds and validates the Streamlit app, and can optionally deploy a live preview for testing.

## 📋 Overview

When you open or update a pull request, GitHub Actions will:

1. ✅ Install dependencies and validate the app
2. 🐳 Build a Docker image
3. 🧪 Test the container health
4. 💬 Comment on the PR with build status
5. 🚀 Deploy a preview (if configured)
6. 🧹 Clean up when the PR is closed

## 🎯 Current Setup

The repository has **three workflow options**:

### 1. Simple Preview (Default) - `.github/workflows/pr-preview-simple.yml`

**Status**: ✅ Active  
**What it does**:
- Validates all PRs automatically
- Builds and tests Docker images
- Provides detailed setup instructions in PR comments
- Works without any additional configuration

This workflow runs automatically and helps reviewers verify that:
- The app builds successfully
- Dependencies are correct
- No import errors exist
- The Docker image is functional

### 2. Full Preview - `.github/workflows/pr-preview.yml`

**Status**: ⏸️ Requires configuration  
**What it does**:
- Everything in Simple Preview, plus:
- Automatically deploys to Streamlit Cloud, Railway, or custom hosting
- Posts live preview URLs in PR comments
- Manages deployment lifecycle

### 3. Render Preview - `.github/workflows/render-preview.yml`

**Status**: ⏸️ Requires configuration  
**What it does**:
- Specifically designed for Render.com
- Creates isolated preview environments per PR
- Automatic cleanup on PR close

## 🔧 Enabling Live Preview Deployments

To enable actual preview deployments with live URLs, configure one of these platforms:

### Option A: Streamlit Community Cloud (Recommended)

Streamlit Community Cloud is purpose-built for Streamlit apps.

**Setup Steps:**

1. **Create Account**
   - Visit [streamlit.io/cloud](https://streamlit.io/cloud)
   - Sign in with GitHub

2. **Manual PR Previews** (Current capability)
   - Each PR creates a new branch
   - You can manually deploy any branch in Streamlit Cloud
   - Share the deployment URL in PR comments

3. **Automated Previews** (Requires API access)
   - Contact Streamlit for API access
   - Add `STREAMLIT_CLOUD_TOKEN` to repository secrets
   - Workflow will auto-deploy on PR

**Pros:**
- Built for Streamlit
- Free tier available
- Simple deployment
- Good performance

**Cons:**
- Limited API access for automation
- May require manual deployment for PRs

### Option B: Render.com

Render provides excellent support for preview environments.

**Setup Steps:**

1. **Create Account**
   - Sign up at [render.com](https://render.com)
   - Free tier includes 750 hours/month

2. **Get API Credentials**
   - Go to [Account Settings](https://dashboard.render.com/account/api-keys)
   - Create a new API key
   - Note your Owner ID from account settings

3. **Configure Repository Secrets**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add secrets:
     - `RENDER_API_KEY`: Your Render API key
     - `RENDER_OWNER_ID`: Your Render owner ID

4. **Enable Workflow**
   - The `render-preview.yml` workflow will activate automatically
   - PRs will now deploy to `paperscope-pr-{number}.onrender.com`

**Pros:**
- Automatic preview environments
- Free tier available
- Good for Docker deployments
- Persistent URLs per PR

**Cons:**
- Free tier has cold starts (services spin down after inactivity)
- May take 5-10 minutes for first deployment

### Option C: Railway.app

Railway offers simple deployment with preview environments.

**Setup Steps:**

1. **Create Account**
   - Sign up at [railway.app](https://railway.app)
   - Free tier: $5 credit per month

2. **Get API Token**
   - Go to [Account Tokens](https://railway.app/account/tokens)
   - Generate new token

3. **Configure Repository Secret**
   - Add `RAILWAY_TOKEN` to repository secrets

4. **Enable Workflow**
   - Update `pr-preview.yml` to use Railway deployment
   - PRs will auto-deploy to Railway preview environments

**Pros:**
- Simple setup
- Good developer experience
- Instant deployments
- Automatic preview URLs

**Cons:**
- Limited free tier
- Requires payment method on file

### Option D: Heroku

Traditional platform with good PR app support.

**Setup Steps:**

1. **Create Account**
   - Sign up at [heroku.com](https://heroku.com)
   - Free tier available (with limitations)

2. **Get API Key**
   - Go to Account Settings
   - Reveal and copy API Key

3. **Configure Repository Secrets**
   - Add `HEROKU_API_KEY` to repository secrets
   - Add `HEROKU_APP_NAME` (prefix for PR apps)

4. **Create Procfile**
   ```
   web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
   ```

**Pros:**
- Mature platform
- Good documentation
- Review apps feature

**Cons:**
- Free tier very limited
- Requires credit card
- Slower cold starts

## 🔐 Security Considerations

### Demo Mode

All preview deployments run in **DEMO_MODE**, which means:

- ✅ No real API keys required
- ✅ Safe for public preview
- ✅ Simplified functionality for testing
- ⚠️ Some features may be limited

### API Keys

The workflows are designed to:

- ❌ Never expose real API keys in PRs from forks
- ✅ Use demo mode for all PR previews
- ✅ Keep production credentials separate
- ✅ Only maintainers can access deployment secrets

### Best Practices

1. **Never commit real API keys** to the repository
2. **Use repository secrets** for deployment tokens
3. **Review PRs** before allowing preview deployments
4. **Monitor usage** on your chosen platform to avoid unexpected costs

## 🧪 Testing Locally

You can test the preview deployment locally:

### Using Python

```bash
# Install dependencies
pip install -r requirements.txt

# Create demo config
cat > paperscope/config.py << EOF
API_KEY = "demo_key"
MODEL = "gemini-pro"
DB_PATH = "db.json"
EOF

# Run in demo mode
DEMO_MODE=1 streamlit run streamlit_app.py
```

### Using Docker

```bash
# Build image
docker build -t paperscope-preview .

# Run container
docker run -p 8501:8501 -e DEMO_MODE=1 paperscope-preview

# Access at http://localhost:8501
```

## 📊 Monitoring Deployments

### GitHub Actions

- View workflow runs: `Actions` tab in GitHub
- Check deployment status: `Environments` tab
- Review logs: Click on any workflow run

### Platform Dashboards

- **Render**: [dashboard.render.com](https://dashboard.render.com)
- **Railway**: [railway.app/dashboard](https://railway.app/dashboard)
- **Streamlit Cloud**: [share.streamlit.io](https://share.streamlit.io)
- **Heroku**: [dashboard.heroku.com](https://dashboard.heroku.com)

## 🐛 Troubleshooting

### Build Failures

If the PR preview build fails:

1. Check the workflow logs in GitHub Actions
2. Verify all dependencies are in `requirements.txt`
3. Test locally with `DEMO_MODE=1`
4. Check for syntax errors or import issues

### Deployment Failures

If deployment fails but build succeeds:

1. Verify secrets are correctly configured
2. Check platform dashboard for errors
3. Review API quotas/limits on your platform
4. Check deployment logs on the platform

### Preview Not Updating

If preview doesn't reflect new commits:

1. Check if workflow is triggered (Actions tab)
2. Verify branch is up to date
3. Force redeploy from platform dashboard
4. Check for workflow file changes

## 💡 Tips for Contributors

1. **Test locally first**: Always test your changes with `DEMO_MODE=1` before pushing
2. **Check build status**: Wait for the build to complete before requesting review
3. **Review preview**: If available, test your changes in the live preview
4. **Ask for help**: If builds fail, ask maintainers for assistance

## 📞 Getting Help

If you need help with preview deployments:

1. **Check workflow logs**: Most issues are visible in GitHub Actions logs
2. **Read platform docs**: Each platform has detailed documentation
3. **Open an issue**: For repository-specific problems
4. **Ask maintainers**: For configuration or secret-related issues

## 🎉 Benefits

Preview deployments provide:

- ✅ **Faster reviews**: Reviewers can test changes live
- ✅ **Better quality**: Catch issues before merging
- ✅ **Easier collaboration**: Share working previews with team
- ✅ **Confidence**: Verify changes work in production-like environment

---

**Note**: The current setup validates all PRs automatically. Live preview URLs require additional configuration by repository maintainers.
