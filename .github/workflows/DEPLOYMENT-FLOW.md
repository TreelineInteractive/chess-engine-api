# GitHub Actions → AWS App Runner Deployment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Developer pushes to main                        │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   GitHub Actions Workflow Starts                    │
│                  (.github/workflows/deploy-apprunner.yml)           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 1: Checkout Code                                              │
│  ├─ actions/checkout@v4                                             │
│  └─ Clones repository to GitHub Actions runner                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 2: Configure AWS Credentials (OIDC)                           │
│  ├─ Uses OpenID Connect (no keys!)                                  │
│  ├─ Assumes role: GitHubActions-AppRunner-Deploy                    │
│  ├─ Trust policy validates: repo + branch                           │
│  └─ Gets temporary AWS credentials (valid ~1 hour)                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 3: Login to Amazon ECR                                        │
│  ├─ Gets ECR auth token                                             │
│  ├─ Configures Docker to use ECR                                    │
│  └─ Registry: 985634834891.dkr.ecr.us-west-2.amazonaws.com         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 4: Build & Push Docker Image                                  │
│  ├─ Platform: linux/amd64                                           │
│  ├─ Multi-stage build (Stockfish + Python)                          │
│  ├─ Tags: [commit-sha], latest                                      │
│  ├─ Layer caching enabled                                           │
│  └─ Push to ECR: chess-engine-api                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 5: Check if App Runner Service Exists                         │
│  ├─ Query: aws apprunner list-services                              │
│  └─ Decision: Create new OR Update existing                         │
└──────────────┬──────────────────────────┬───────────────────────────┘
               │                          │
      (New)    │                          │    (Exists)
               ▼                          ▼
┌─────────────────────────┐  ┌────────────────────────────────────┐
│  Create Service         │  │  Update Service                    │
│  ├─ Image from ECR      │  │  ├─ New image from ECR             │
│  ├─ 1 vCPU, 2 GB        │  │  ├─ Keep configuration             │
│  ├─ Port: 8000          │  │  └─ Rolling deployment             │
│  ├─ Health: /health     │  └────────────────┬───────────────────┘
│  ├─ Env vars (17 vars)  │                   │
│  └─ Network: DEFAULT    │                   │
└──────────┬──────────────┘                   │
           │                                  │
           └──────────────┬───────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 6: Wait for Deployment                                        │
│  ├─ Poll every 10 seconds                                           │
│  ├─ Max wait: 10 minutes                                            │
│  ├─ Check status: RUNNING, FAILED, etc.                             │
│  └─ Exit on: RUNNING (success) or FAILED (error)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 7: Configure Custom Domain                                    │
│  ├─ Domain: chessengine.treelineint.click                          │
│  ├─ Associate with App Runner service                               │
│  ├─ Get DNS validation records                                      │
│  └─ Auto-generates TLS certificate                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 8: Update Route 53 DNS                                        │
│  ├─ Hosted zone: treelineint.click (Z07869121BWALG9IZ0R7I)         │
│  ├─ Create/Update CNAME record                                      │
│  ├─ Target: [app-runner-url].us-west-2.awsapprunner.com           │
│  └─ TTL: 300 seconds                                                │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 9: Health Check                                               │
│  ├─ URL: https://[service-url]/api/v1/health                       │
│  ├─ Retry: 30 attempts x 10 seconds                                │
│  ├─ Expect: HTTP 200                                                │
│  └─ Verify: Service is responding                                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Step 10: Deployment Summary                                        │
│  ├─ Service ARN                                                     │
│  ├─ Service URL                                                     │
│  ├─ Custom Domain URL                                               │
│  ├─ Image SHA                                                       │
│  └─ Health check results                                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    ✅ Deployment Complete!                          │
│                                                                     │
│  🌐 https://chessengine.treelineint.click                          │
│  📊 View in GitHub Actions                                          │
│  🔍 Monitor in CloudWatch                                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Key Components

### AWS Resources
- **OIDC Provider**: `token.actions.githubusercontent.com`
- **GitHub Actions Role**: `GitHubActions-AppRunner-Deploy`
- **App Runner Access Role**: `AppRunnerECRAccessRole`
- **ECR Repository**: `chess-engine-api`
- **App Runner Service**: `chess-engine-api`
- **Route 53 Zone**: `treelineint.click`
- **Custom Domain**: `chessengine.treelineint.click`

### Security Flow
```
GitHub Actions Runner
    │
    │ (OIDC Token)
    ▼
AWS STS (Security Token Service)
    │
    │ Validates:
    │  ├─ Repository: TreelineInteractive/chess-engine-api
    │  ├─ Branch: refs/heads/main
    │  └─ OIDC Provider thumbprint
    │
    ▼
Temporary AWS Credentials
    │
    │ (Valid ~1 hour)
    ▼
AWS Services (ECR, App Runner, Route 53)
```

### Build & Deploy Pipeline
```
Source Code
    │
    ▼
Dockerfile (Multi-stage)
    │
    ├─ Stage 1: Build Stockfish (Ubuntu 22.04)
    │   ├─ Download Stockfish 17.1
    │   ├─ Compile for architecture
    │   └─ Output: /tmp/stockfish binary
    │
    └─ Stage 2: Python App (Python 3.11-slim)
        ├─ Copy Stockfish binary
        ├─ Install dependencies
        ├─ Copy application code
        └─ Expose port 8000
    │
    ▼
Container Image
    │
    ├─ Tag: [commit-sha]
    └─ Tag: latest
    │
    ▼
Amazon ECR
    │
    ├─ Scan for vulnerabilities
    └─ Store with encryption
    │
    ▼
AWS App Runner
    │
    ├─ Pull image from ECR
    ├─ Deploy to managed containers
    ├─ Auto-scale based on traffic
    └─ Health check on /api/v1/health
    │
    ▼
Production (HTTPS)
    │
    ├─ https://[random].us-west-2.awsapprunner.com
    └─ https://chessengine.treelineint.click
```

## Rollback Strategy

```
Production Issue Detected
    │
    ├─ Option 1: Revert Git Commit
    │   └─ Push revert → Auto-deploys previous version
    │
    ├─ Option 2: AWS Console
    │   └─ App Runner → Deployments → Select previous version
    │
    └─ Option 3: AWS CLI
        └─ aws apprunner start-deployment --service-arn [ARN]
```

## Monitoring & Observability

```
┌──────────────────────┐
│  Application Logs    │
│  (App Runner)        │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  CloudWatch Logs     │
│  /aws/apprunner/     │
│  chess-engine-api    │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  CloudWatch Metrics  │
│  ├─ CPU              │
│  ├─ Memory           │
│  ├─ Request count    │
│  ├─ Response time    │
│  └─ HTTP status      │
└──────────────────────┘

┌──────────────────────┐
│  GitHub Actions      │
│  ├─ Workflow runs    │
│  ├─ Deployment logs  │
│  └─ Job summaries    │
└──────────────────────┘
```

## Cost Breakdown

```
Monthly Costs (estimated):

App Runner:
  ├─ Provisioned capacity: 1 vCPU, 2 GB
  │   └─ ~$25/month (continuous running)
  │
  ├─ Active requests: Pay per use
  │   └─ ~$5-20/month (depends on traffic)
  │
  └─ Total: ~$30-45/month

ECR:
  ├─ Storage: ~500 MB
  │   └─ ~$0.05/month
  │
  └─ Data transfer: Included to App Runner

Route 53:
  └─ Hosted zone: $0.50/month

────────────────────────────────
TOTAL: ~$31-46/month
```
