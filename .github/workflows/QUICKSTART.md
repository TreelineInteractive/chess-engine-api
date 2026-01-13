# Quick Start Guide - AWS App Runner Deployment

## 🚀 Quick Setup (5 minutes)

### Step 1: Test AWS Connectivity ✅ DONE
```bash
./.github/workflows/test-aws-connectivity.sh
```
**Status**: Credentials validated, account 985634834891 confirmed

### Step 2: Run AWS Setup Script
```bash
cd .github/workflows
./setup-aws-oidc.sh
```

This will output two ARNs that you need for GitHub Secrets.

### Step 3: Add GitHub Secrets

#### Option A: Using GitHub CLI (Recommended)
```bash
# Copy the ARNs from the setup script output, then:
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::985634834891:role/GitHubActions-AppRunner-Deploy"
gh secret set APP_RUNNER_ACCESS_ROLE_ARN --body "arn:aws:iam::985634834891:role/AppRunnerECRAccessRole"
```

#### Option B: Using GitHub Web UI
1. Go to: https://github.com/TreelineInteractive/chess-engine-api/settings/secrets/actions
2. Click "New repository secret"
3. Add both secrets from setup script output

### Step 4: Deploy!
```bash
git add .
git commit -m "Add App Runner deployment workflow"
git push origin main
```

Watch the deployment at:
https://github.com/TreelineInteractive/chess-engine-api/actions

---

## 📋 What Was Created

### Files Created:
- ✅ `.github/workflows/deploy-apprunner.yml` - Main deployment workflow
- ✅ `.github/workflows/setup-aws-oidc.sh` - AWS resource setup script
- ✅ `.github/workflows/README.md` - Comprehensive documentation
- ✅ `.github/workflows/test-aws-connectivity.sh` - Connectivity test (in .gitignore)

### AWS Resources to be Created:
- 🔧 GitHub OIDC Provider (already exists)
- 🔧 ECR Repository: `chess-engine-api`
- 🔧 IAM Role: `GitHubActions-AppRunner-Deploy`
- 🔧 IAM Role: `AppRunnerECRAccessRole`
- 🔧 IAM Policy: `GitHubActions-AppRunner-Deploy-Policy`
- 🔧 App Runner Service: `chess-engine-api`
- 🔧 Route 53 Record: `chessengine.treelineint.click`

### Existing Resources Found:
- ✅ OIDC Provider: `arn:aws:iam::985634834891:oidc-provider/token.actions.githubusercontent.com`
- ✅ Hosted Zone: `treelineint.click` (Z07869121BWALG9IZ0R7I)
- ✅ AWS Account: 985634834891
- ✅ Region: us-west-2

---

## 🎯 After Deployment

Your API will be available at:
- **Custom Domain**: https://chessengine.treelineint.click
- **App Runner URL**: https://[random-id].us-west-2.awsapprunner.com

Test it:
```bash
curl https://chessengine.treelineint.click/api/v1/health
```

---

## 🔍 Monitoring

### View Logs
```bash
# Real-time logs
aws logs tail /aws/apprunner/chess-engine-api --follow --region us-west-2

# Service status
aws apprunner list-services --region us-west-2
```

### GitHub Actions
Monitor deployments: https://github.com/TreelineInteractive/chess-engine-api/actions

---

## 🛠 Common Commands

### Manual Deploy
```bash
# Trigger from GitHub UI or:
gh workflow run deploy-apprunner.yml
```

### Check Service Status
```bash
export SERVICE_ARN=$(aws apprunner list-services --region us-west-2 \
  --query "ServiceSummaryList[?ServiceName=='chess-engine-api'].ServiceArn" \
  --output text)

aws apprunner describe-service --service-arn $SERVICE_ARN --region us-west-2
```

### Update Environment Variables
Edit `.github/workflows/deploy-apprunner.yml` and push to main.

---

## 📦 Configuration

### Instance Size
Current: **1 vCPU, 2 GB RAM**

To modify, edit the `instance-configuration` in `deploy-apprunner.yml`:
```yaml
--instance-configuration '{
  "Cpu": "2 vCPU",      # Options: 0.25, 0.5, 1, 2, 4 vCPU
  "Memory": "4 GB"       # Options: 0.5, 1, 2, 3, 4, 6, 8, 10, 12 GB
}'
```

### Auto Scaling
App Runner automatically scales based on traffic (managed by AWS).

---

## 🔐 Security Notes

- ✅ Using OIDC (no long-lived credentials)
- ✅ ECR image scanning enabled
- ✅ IAM roles follow least privilege
- ✅ Only main branch can deploy
- ✅ HTTPS enforced on custom domain

---

## ❓ Troubleshooting

### Deployment fails?
1. Check GitHub Actions logs
2. Verify secrets are set correctly
3. Check AWS CloudWatch logs

### Domain not working?
- DNS propagation can take up to 48 hours (usually < 1 hour)
- Check Route 53 records: `aws route53 list-resource-record-sets --hosted-zone-id Z07869121BWALG9IZ0R7I`

### Need to rollback?
App Runner keeps previous versions. Use AWS Console to rollback or:
```bash
aws apprunner start-deployment --service-arn $SERVICE_ARN --region us-west-2
```

---

## 📞 Support

- Full documentation: `.github/workflows/README.md`
- AWS Console: https://console.aws.amazon.com/apprunner
- GitHub Actions: https://github.com/TreelineInteractive/chess-engine-api/actions
