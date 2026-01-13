# AWS App Runner Deployment - Setup Complete! 🚀

## Summary

I've created a complete GitHub Actions workflow for deploying your Chess Engine API to AWS App Runner using OIDC authentication. The deployment will use the domain `chessengine.treelineint.click` in the `us-west-2` region.

---

## 📁 Files Created

### GitHub Workflows (`.github/workflows/`)
1. **`deploy-apprunner.yml`** - Main deployment workflow
   - Triggers on push to `main` branch
   - Uses OIDC for secure AWS authentication
   - Builds and pushes Docker images to ECR
   - Creates/updates App Runner service
   - Configures custom domain with Route 53
   - Includes health checks and deployment summaries

2. **`validate-deployment.yml`** - PR validation workflow
   - Runs on pull requests to `main`
   - Validates Dockerfile, dependencies, and workflow configuration
   - Ensures deployment readiness before merging

3. **`setup-aws-oidc.sh`** - AWS resource setup script (executable)
   - Creates OIDC provider
   - Creates ECR repository
   - Creates IAM roles and policies
   - Outputs ARNs for GitHub Secrets

4. **`test-aws-connectivity.sh`** - Connectivity test script (executable, in .gitignore)
   - Tests AWS credentials
   - Checks existing resources
   - **Status**: ✅ Already tested successfully with your credentials

5. **`README.md`** - Comprehensive documentation
   - Setup instructions
   - Troubleshooting guide
   - Monitoring and management commands
   - Security best practices

6. **`QUICKSTART.md`** - Quick reference guide
   - Step-by-step setup (5 minutes)
   - Common commands
   - Post-deployment checklist

### Configuration Files
7. **`.dockerignore`** - Docker build optimization
   - Excludes unnecessary files from build context
   - Reduces image size and build time

8. **`.gitignore`** - Updated to exclude test script with credentials

---

## ✅ Pre-Flight Check Results

Using your provided AWS credentials, I verified:

- ✅ **AWS Account**: 985634834891
- ✅ **Region**: us-west-2
- ✅ **Credentials**: Valid (assumed role: AWSReservedSSO_trl-org-admins)
- ✅ **OIDC Provider**: Already exists in your account
- ✅ **Route 53 Hosted Zone**: `treelineint.click` (22 records)
- ✅ **Existing ECR Repos**: Found (boilerplate-staging, sst-asset, etc.)
- ✅ **App Runner Services**: None (will be created on first deploy)

---

## 🎯 Next Steps

### 1. Run the AWS Setup Script
```bash
cd .github/workflows
./setup-aws-oidc.sh
```

This will create:
- ECR repository: `chess-engine-api`
- IAM Role: `GitHubActions-AppRunner-Deploy`
- IAM Role: `AppRunnerECRAccessRole`
- IAM Policy: `GitHubActions-AppRunner-Deploy-Policy`

### 2. Add GitHub Secrets

The setup script will output two ARNs. Add them to GitHub:

```bash
# Using GitHub CLI (recommended)
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::985634834891:role/GitHubActions-AppRunner-Deploy"
gh secret set APP_RUNNER_ACCESS_ROLE_ARN --body "arn:aws:iam::985634834891:role/AppRunnerECRAccessRole"
```

Or manually at: https://github.com/TreelineInteractive/chess-engine-api/settings/secrets/actions

### 3. Commit and Push

```bash
git add .
git commit -m "Add AWS App Runner deployment workflow"
git push origin main
```

### 4. Monitor Deployment

Watch the deployment progress at:
https://github.com/TreelineInteractive/chess-engine-api/actions

---

## 🌐 Deployment Endpoints

After successful deployment, your API will be available at:

- **Custom Domain**: https://chessengine.treelineint.click
- **Health Check**: https://chessengine.treelineint.click/api/v1/health
- **App Runner URL**: https://[random-id].us-west-2.awsapprunner.com (auto-assigned)

---

## ⚙️ Configuration

### Instance Configuration
- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Auto-scaling**: Enabled (managed by App Runner)
- **Health Check**: HTTP `/api/v1/health` (interval: 10s, timeout: 5s)

### Environment Variables
Pre-configured in the workflow:
```yaml
STOCKFISH_PATH: /usr/local/bin/stockfish
STOCKFISH_THREADS: 2
STOCKFISH_HASH_SIZE_MB: 256
STOCKFISH_SKILL_LEVEL: 20
MAX_DEPTH: 25
DEFAULT_DEPTH: 15
MAX_ANALYSIS_TIME_MS: 10000
MAX_MULTI_PV: 5
API_VERSION: 1.0.0
API_RATE_LIMIT_PER_MINUTE: 100
MAX_CONCURRENT_ANALYSES: 10
HOST: 0.0.0.0
PORT: 8000
DEBUG: false
CORS_ORIGINS: "*"
LOG_LEVEL: INFO
LOG_FORMAT: json
```

---

## 🔐 Security Features

✅ **OIDC Authentication**: No long-lived AWS credentials in GitHub
✅ **IAM Least Privilege**: Minimal permissions for each role
✅ **Branch Protection**: Only `main` branch can deploy
✅ **ECR Image Scanning**: Automatic vulnerability scanning
✅ **HTTPS Only**: All traffic encrypted with TLS
✅ **Secret Management**: Sensitive values in GitHub Secrets

---

## 📊 Workflow Features

### On Every Push to Main:
1. ✅ Checkout code
2. ✅ Authenticate to AWS via OIDC
3. ✅ Login to ECR
4. ✅ Build multi-arch Docker image (linux/amd64)
5. ✅ Push to ECR with image tagging (commit SHA + latest)
6. ✅ Create or update App Runner service
7. ✅ Wait for deployment to complete
8. ✅ Configure custom domain (chessengine.treelineint.click)
9. ✅ Update Route 53 DNS records
10. ✅ Run health checks
11. ✅ Generate deployment summary

### On Pull Requests:
- ✅ Validate Dockerfile syntax
- ✅ Check required files exist
- ✅ Validate workflow YAML
- ✅ Check Python dependencies
- ✅ Verify build context

---

## 📚 Documentation

- **Quick Start**: `.github/workflows/QUICKSTART.md`
- **Full Guide**: `.github/workflows/README.md`
- **Deployment Workflow**: `.github/workflows/deploy-apprunner.yml`
- **Validation Workflow**: `.github/workflows/validate-deployment.yml`

---

## 🛠 Management Commands

### View Service Status
```bash
aws apprunner list-services --region us-west-2
```

### View Logs
```bash
aws logs tail /aws/apprunner/chess-engine-api --follow --region us-west-2
```

### Manual Deployment
```bash
gh workflow run deploy-apprunner.yml
```

### Check DNS Records
```bash
aws route53 list-resource-record-sets --hosted-zone-id Z07869121BWALG9IZ0R7I
```

---

## 💰 Cost Estimate

AWS App Runner pricing (as of 2026):
- **Provisioned**: ~$0.007/hour for 1 vCPU, 2 GB
- **Compute**: ~$0.064 per vCPU-hour
- **Memory**: ~$0.007 per GB-hour

**Estimated monthly cost**: ~$25-50 depending on traffic

ECR storage: ~$0.10/GB per month
Route 53: $0.50 per hosted zone per month

---

## 🎉 What Makes This Special

1. **Zero Credential Management**: Uses OIDC, no AWS keys in GitHub
2. **Fully Automated**: One push deploys everything
3. **Production Ready**: Health checks, monitoring, auto-scaling
4. **Custom Domain**: Automatic DNS configuration
5. **Docker Optimized**: Multi-stage build, layer caching
6. **Validated**: PR checks ensure deployment readiness
7. **Well Documented**: Multiple guides for different needs

---

## 📞 Support & Troubleshooting

If you encounter issues:
1. Check `.github/workflows/README.md` troubleshooting section
2. Review GitHub Actions logs
3. Check AWS CloudWatch logs
4. Verify secrets are set correctly
5. Ensure IAM roles have correct trust policies

---

## 🚦 Ready to Deploy!

Everything is set up and ready to go. Just run the setup script, add the secrets, and push to `main`!

**Questions?** Check the documentation files or the workflow comments for detailed explanations.

---

**Created**: January 13, 2026
**Repository**: TreelineInteractive/chess-engine-api
**AWS Account**: 985634834891
**Region**: us-west-2
**Domain**: chessengine.treelineint.click
