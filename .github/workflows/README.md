# AWS App Runner Deployment with GitHub Actions OIDC

This directory contains GitHub Actions workflows for deploying the Chess Engine API to AWS App Runner using OIDC (OpenID Connect) authentication.

## Overview

The deployment workflow:
- Triggers on pushes to the `main` branch
- Uses OIDC for secure, keyless authentication to AWS
- Builds and pushes Docker images to Amazon ECR
- Deploys to AWS App Runner in us-west-2
- Configures custom domain: `chessengine.treelineint.click`
- Includes health checks and deployment summaries

## Prerequisites

1. AWS Account with appropriate permissions
2. GitHub repository: `TreelineInteractive/chess-engine-api`
3. Route 53 hosted zone for `treelineint.click`
4. AWS CLI installed and configured
5. (Optional) GitHub CLI for setting secrets

## Initial Setup

### 1. Run the AWS Setup Script

The setup script creates all necessary AWS resources:

```bash
cd .github/workflows
chmod +x setup-aws-oidc.sh
./setup-aws-oidc.sh
```

This script will:
- ✅ Create GitHub OIDC Identity Provider in AWS
- ✅ Create ECR repository for Docker images
- ✅ Create IAM role for GitHub Actions with OIDC trust policy
- ✅ Create IAM role for App Runner to access ECR
- ✅ Attach necessary permissions policies

### 2. Add GitHub Secrets

After running the setup script, add these secrets to your GitHub repository:

**Method 1: Using GitHub CLI**
```bash
# The setup script will output these commands
gh secret set AWS_ROLE_ARN --body "arn:aws:iam::ACCOUNT_ID:role/GitHubActions-AppRunner-Deploy"
gh secret set APP_RUNNER_ACCESS_ROLE_ARN --body "arn:aws:iam::ACCOUNT_ID:role/AppRunnerECRAccessRole"
```

**Method 2: Using GitHub Web UI**
1. Go to: `https://github.com/TreelineInteractive/chess-engine-api/settings/secrets/actions`
2. Click "New repository secret"
3. Add:
   - **Name**: `AWS_ROLE_ARN`
   - **Value**: The ARN output from the setup script
4. Add:
   - **Name**: `APP_RUNNER_ACCESS_ROLE_ARN`
   - **Value**: The ARN output from the setup script

### 3. Verify Route 53 Hosted Zone

Ensure you have a hosted zone for `treelineint.click`:

```bash
aws route53 list-hosted-zones --query "HostedZones[?Name=='treelineint.click.']"
```

## Deployment

### Automatic Deployment

The workflow automatically deploys when you push to the `main` branch:

```bash
git add .
git commit -m "Update application"
git push origin main
```

### Manual Deployment

Trigger a deployment manually from GitHub:

1. Go to: `https://github.com/TreelineInteractive/chess-engine-api/actions`
2. Select "Deploy to AWS App Runner"
3. Click "Run workflow"
4. Select branch: `main`
5. Click "Run workflow"

## Testing with Temporary Credentials

For initial testing, you can use temporary AWS credentials:

```bash
export AWS_ACCESS_KEY_ID="YOUR_ACCESS_KEY"
export AWS_SECRET_ACCESS_KEY="YOUR_SECRET_KEY"
export AWS_SESSION_TOKEN="YOUR_SESSION_TOKEN"
export AWS_REGION="us-west-2"

# Test ECR login
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Test App Runner service listing
aws apprunner list-services --region us-west-2
```

## Workflow Details

### Workflow File
- **Location**: `.github/workflows/deploy-apprunner.yml`
- **Trigger**: Push to `main` branch or manual dispatch
- **Region**: us-west-2
- **Service**: AWS App Runner

### Deployment Steps

1. **Checkout Code**: Clones the repository
2. **Configure AWS Credentials**: Uses OIDC to assume the AWS role
3. **Login to ECR**: Authenticates with Amazon Elastic Container Registry
4. **Build & Push Image**: Builds Docker image and pushes to ECR
5. **Create/Update Service**: Creates new App Runner service or updates existing
6. **Wait for Deployment**: Monitors deployment status
7. **Configure Domain**: Sets up custom domain with Route 53
8. **Health Check**: Verifies the service is healthy
9. **Summary**: Provides deployment details

### Environment Variables

The workflow configures these environment variables in App Runner:

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

### Instance Configuration

- **CPU**: 1 vCPU
- **Memory**: 2 GB
- **Health Check**: HTTP on `/api/v1/health`
- **Port**: 8000

## Accessing the Deployment

After successful deployment, your API will be available at:

- **App Runner URL**: `https://RANDOM_ID.us-west-2.awsapprunner.com`
- **Custom Domain**: `https://chessengine.treelineint.click`

### Health Check Endpoints

```bash
# App Runner default URL
curl https://RANDOM_ID.us-west-2.awsapprunner.com/api/v1/health

# Custom domain
curl https://chessengine.treelineint.click/api/v1/health
```

## Monitoring and Logs

### View App Runner Logs

```bash
# Get service ARN
SERVICE_ARN=$(aws apprunner list-services --region us-west-2 \
  --query "ServiceSummaryList[?ServiceName=='chess-engine-api'].ServiceArn" \
  --output text)

# Describe service
aws apprunner describe-service --service-arn $SERVICE_ARN --region us-west-2

# View logs in CloudWatch
aws logs tail /aws/apprunner/chess-engine-api --follow --region us-west-2
```

### GitHub Actions Logs

View workflow execution logs at:
`https://github.com/TreelineInteractive/chess-engine-api/actions`

## Troubleshooting

### OIDC Authentication Fails

1. Verify the OIDC provider exists:
   ```bash
   aws iam list-open-id-connect-providers
   ```

2. Check the role trust policy allows the correct repository:
   ```bash
   aws iam get-role --role-name GitHubActions-AppRunner-Deploy
   ```

### ECR Push Fails

1. Verify ECR repository exists:
   ```bash
   aws ecr describe-repositories --repository-names chess-engine-api --region us-west-2
   ```

2. Test ECR authentication:
   ```bash
   aws ecr get-login-password --region us-west-2
   ```

### App Runner Deployment Fails

1. Check service status:
   ```bash
   aws apprunner describe-service --service-arn $SERVICE_ARN --region us-west-2
   ```

2. View recent operations:
   ```bash
   aws apprunner list-operations --service-arn $SERVICE_ARN --region us-west-2
   ```

### Custom Domain Issues

1. Verify DNS records in Route 53:
   ```bash
   aws route53 list-resource-record-sets --hosted-zone-id ZONE_ID
   ```

2. Check custom domain status:
   ```bash
   aws apprunner describe-custom-domains \
     --service-arn $SERVICE_ARN \
     --region us-west-2
   ```

## Security Best Practices

1. **OIDC vs Access Keys**: This setup uses OIDC which is more secure than long-lived access keys
2. **Least Privilege**: IAM roles have minimal required permissions
3. **Branch Protection**: Only `main` branch can trigger deployments
4. **Secret Management**: Sensitive values stored in GitHub Secrets
5. **Image Scanning**: ECR automatically scans images for vulnerabilities

## Cost Optimization

- App Runner pricing: Pay only for what you use
- Instance size can be adjusted in the workflow
- Auto-scaling built into App Runner
- ECR lifecycle policies can clean up old images

## Updating the Workflow

To modify deployment configuration:

1. Edit `.github/workflows/deploy-apprunner.yml`
2. Commit and push to `main`
3. The workflow will use the new configuration on next deployment

## Cleanup

To remove all AWS resources:

```bash
# Delete App Runner service
aws apprunner delete-service --service-arn $SERVICE_ARN --region us-west-2

# Delete ECR repository
aws ecr delete-repository --repository-name chess-engine-api --region us-west-2 --force

# Detach and delete policies
aws iam detach-role-policy --role-name GitHubActions-AppRunner-Deploy \
  --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActions-AppRunner-Deploy-Policy
aws iam delete-policy --policy-arn arn:aws:iam::ACCOUNT_ID:policy/GitHubActions-AppRunner-Deploy-Policy

# Delete roles
aws iam delete-role --role-name GitHubActions-AppRunner-Deploy
aws iam delete-role --role-name AppRunnerECRAccessRole
```

## Additional Resources

- [AWS App Runner Documentation](https://docs.aws.amazon.com/apprunner/)
- [GitHub Actions OIDC](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)
- [ECR User Guide](https://docs.aws.amazon.com/ecr/)
- [Route 53 Documentation](https://docs.aws.amazon.com/route53/)

## Support

For issues or questions:
1. Check GitHub Actions logs
2. Review CloudWatch logs
3. Consult AWS App Runner console
4. Open an issue in the repository
