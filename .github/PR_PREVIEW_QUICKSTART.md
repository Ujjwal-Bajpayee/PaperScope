# Quick Start: PR Preview Setup

This is a quick reference for maintainers to enable live PR preview deployments.

## ⚡ Quick Setup Options

### Option 1: Render.com (5 minutes)

Render is recommended for its simplicity and good free tier.

```bash
# 1. Create Render account at render.com
# 2. Get API key from dashboard.render.com/account/api-keys
# 3. Add secrets to GitHub repo:

gh secret set RENDER_API_KEY --body "YOUR_API_KEY"
gh secret set RENDER_OWNER_ID --body "YOUR_OWNER_ID"

# 4. That's it! PRs will now auto-deploy to Render
```

Preview URLs will be: `https://paperscope-pr-{number}.onrender.com`

### Option 2: Railway.app (3 minutes)

```bash
# 1. Create Railway account at railway.app
# 2. Get token from railway.app/account/tokens
# 3. Add secret:

gh secret set RAILWAY_TOKEN --body "YOUR_TOKEN"

# 4. Done! Railway will create preview environments
```

### Option 3: Streamlit Cloud (Manual)

```bash
# 1. Go to streamlit.io/cloud
# 2. Connect GitHub repository
# 3. For each PR, manually deploy the PR branch
# 4. Share the deployment URL in PR comments
```

Note: Streamlit Cloud doesn't currently support automated PR deployments via API.

## 🔍 Verification

After setup, test with a dummy PR:

1. Create a test branch
2. Make a small change
3. Open a PR
4. Check Actions tab for workflow run
5. Look for preview URL in PR comment
6. Close PR and verify cleanup

## 🎯 What Happens Automatically

Once configured:

1. **PR Opened** → Build + Deploy + Comment with URL
2. **PR Updated** → Redeploy + Update comment
3. **PR Closed** → Cleanup deployment + Comment confirmation

## 📊 Cost Estimates

| Platform | Free Tier | Cost After |
|----------|-----------|------------|
| Render | 750 hrs/month | $7/month per service |
| Railway | $5 credit/month | Pay as you go |
| Streamlit Cloud | Limited deployments | Contact sales |
| Heroku | Very limited | $7/month per dyno |

For a repository with ~10 PRs/month:
- **Render**: Should stay within free tier
- **Railway**: Might need $5-10/month
- **Streamlit Cloud**: Free if manual deployment is acceptable

## 🔐 Security Note

The workflows are designed to:
- Run PR builds in isolated environments
- Use DEMO_MODE (no real API keys needed)
- Only allow maintainers to access deployment secrets
- Prevent secrets exposure in forked PR builds

## 📝 Files Created

This PR preview setup includes:

```
.github/
├── workflows/
│   ├── pr-preview-simple.yml    # Main workflow (always runs)
│   ├── pr-preview.yml           # Full deployment workflow
│   └── render-preview.yml       # Render-specific workflow
├── PREVIEW_DEPLOYMENTS.md       # Full documentation
└── PR_PREVIEW_QUICKSTART.md    # This file

Dockerfile                        # Container definition
.dockerignore                     # Docker build optimization
render.yaml                       # Render blueprint configuration
```

## 🆘 Troubleshooting

**Problem**: Workflow runs but no preview URL

**Solution**: Check that secrets are set correctly:
```bash
gh secret list
```

**Problem**: Deployment fails with auth error

**Solution**: Verify API key/token is still valid on the platform

**Problem**: Preview is slow or timing out

**Solution**: Free tiers have cold starts. Wait 30-60 seconds after first deploy.

## 📞 Need Help?

1. Check [PREVIEW_DEPLOYMENTS.md](.github/PREVIEW_DEPLOYMENTS.md) for detailed docs
2. Review workflow logs in Actions tab
3. Check platform dashboard for deployment status
4. Open an issue if problems persist

---

**Status**: Currently validating PRs automatically. Live URLs require platform configuration above.
