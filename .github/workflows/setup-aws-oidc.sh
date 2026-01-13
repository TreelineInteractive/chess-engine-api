#!/bin/bash
set -e

# AWS App Runner OIDC Setup Script
# This script creates the necessary AWS resources for GitHub Actions OIDC authentication

GITHUB_ORG="TreelineInteractive"
GITHUB_REPO="chess-engine-api"
AWS_REGION="us-west-2"
ECR_REPOSITORY="chess-engine-api"

echo "Setting up AWS resources for GitHub Actions OIDC..."
echo "GitHub Org/Repo: $GITHUB_ORG/$GITHUB_REPO"
echo "AWS Region: $AWS_REGION"
echo ""

# 1. Create OIDC Identity Provider (if not exists)
echo "Step 1: Checking GitHub OIDC Provider..."
OIDC_PROVIDER_ARN=$(aws iam list-open-id-connect-providers \
  --query "OpenIDConnectProviderList[?contains(Arn, 'token.actions.githubusercontent.com')].Arn" \
  --output text)

if [ -z "$OIDC_PROVIDER_ARN" ]; then
  echo "Creating GitHub OIDC Provider..."
  OIDC_PROVIDER_ARN=$(aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 1c58a3a8518e8759bf075b76b750d4f2df264fcd \
    --query 'OpenIDConnectProviderArn' \
    --output text)
  echo "✅ Created OIDC Provider: $OIDC_PROVIDER_ARN"
else
  echo "✅ OIDC Provider already exists: $OIDC_PROVIDER_ARN"
fi

# 2. Create ECR Repository (if not exists)
echo ""
echo "Step 2: Checking ECR Repository..."
if aws ecr describe-repositories --repository-names $ECR_REPOSITORY --region $AWS_REGION >/dev/null 2>&1; then
  echo "✅ ECR Repository already exists: $ECR_REPOSITORY"
else
  echo "Creating ECR Repository..."
  aws ecr create-repository \
    --repository-name $ECR_REPOSITORY \
    --region $AWS_REGION \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
  echo "✅ Created ECR Repository: $ECR_REPOSITORY"
fi

ECR_REPOSITORY_ARN=$(aws ecr describe-repositories \
  --repository-names $ECR_REPOSITORY \
  --region $AWS_REGION \
  --query 'repositories[0].repositoryArn' \
  --output text)

# 3. Create GitHub Actions OIDC Role
echo ""
echo "Step 3: Creating GitHub Actions OIDC Role..."

TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "$OIDC_PROVIDER_ARN"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:$GITHUB_ORG/$GITHUB_REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
EOF
)

ROLE_NAME="GitHubActions-AppRunner-Deploy"

# Check if role exists
if aws iam get-role --role-name $ROLE_NAME >/dev/null 2>&1; then
  echo "Role already exists, updating trust policy..."
  echo "$TRUST_POLICY" > /tmp/trust-policy.json
  aws iam update-assume-role-policy \
    --role-name $ROLE_NAME \
    --policy-document file:///tmp/trust-policy.json
else
  echo "Creating new role..."
  echo "$TRUST_POLICY" > /tmp/trust-policy.json
  aws iam create-role \
    --role-name $ROLE_NAME \
    --assume-role-policy-document file:///tmp/trust-policy.json \
    --description "Role for GitHub Actions to deploy to App Runner"
fi

GITHUB_ROLE_ARN=$(aws iam get-role --role-name $ROLE_NAME --query 'Role.Arn' --output text)
echo "✅ GitHub Actions Role ARN: $GITHUB_ROLE_ARN"

# 4. Create and attach policy for GitHub Actions role
echo ""
echo "Step 4: Attaching policies to GitHub Actions role..."

POLICY_NAME="GitHubActions-AppRunner-Deploy-Policy"
POLICY_DOCUMENT=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:DescribeRepositories",
        "ecr:ListImages"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apprunner:CreateService",
        "apprunner:UpdateService",
        "apprunner:DescribeService",
        "apprunner:ListServices",
        "apprunner:AssociateCustomDomain",
        "apprunner:DescribeCustomDomains",
        "apprunner:ListCustomDomains",
        "apprunner:TagResource",
        "apprunner:ListTagsForResource"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "route53:ListHostedZones",
        "route53:ListResourceRecordSets",
        "route53:ChangeResourceRecordSets",
        "route53:GetChange"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/AppRunnerECRAccessRole"
    }
  ]
}
EOF
)

# Check if policy exists, create or update
POLICY_ARN=$(aws iam list-policies \
  --scope Local \
  --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" \
  --output text)

if [ -z "$POLICY_ARN" ]; then
  echo "Creating new policy..."
  echo "$POLICY_DOCUMENT" > /tmp/policy.json
  POLICY_ARN=$(aws iam create-policy \
    --policy-name $POLICY_NAME \
    --policy-document file:///tmp/policy.json \
    --query 'Policy.Arn' \
    --output text)
else
  echo "Policy already exists, creating new version..."
  echo "$POLICY_DOCUMENT" > /tmp/policy.json
  aws iam create-policy-version \
    --policy-arn $POLICY_ARN \
    --policy-document file:///tmp/policy.json \
    --set-as-default
fi

# Attach policy to role
aws iam attach-role-policy \
  --role-name $ROLE_NAME \
  --policy-arn $POLICY_ARN

echo "✅ Attached policy: $POLICY_ARN"

# 5. Create App Runner ECR Access Role
echo ""
echo "Step 5: Creating App Runner ECR Access Role..."

APPRUNNER_ROLE_NAME="AppRunnerECRAccessRole"
APPRUNNER_TRUST_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "build.apprunner.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

if aws iam get-role --role-name $APPRUNNER_ROLE_NAME >/dev/null 2>&1; then
  echo "App Runner role already exists"
else
  echo "Creating App Runner ECR Access Role..."
  echo "$APPRUNNER_TRUST_POLICY" > /tmp/apprunner-trust.json
  aws iam create-role \
    --role-name $APPRUNNER_ROLE_NAME \
    --assume-role-policy-document file:///tmp/apprunner-trust.json \
    --description "Role for App Runner to access ECR"
fi

# Attach AWS managed policy for ECR access
aws iam attach-role-policy \
  --role-name $APPRUNNER_ROLE_NAME \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess

APPRUNNER_ROLE_ARN=$(aws iam get-role --role-name $APPRUNNER_ROLE_NAME --query 'Role.Arn' --output text)
echo "✅ App Runner ECR Access Role ARN: $APPRUNNER_ROLE_ARN"

# Cleanup temp files
rm -f /tmp/trust-policy.json /tmp/policy.json /tmp/apprunner-trust.json

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "Add these secrets to your GitHub repository:"
echo ""
echo "AWS_ROLE_ARN=$GITHUB_ROLE_ARN"
echo "APP_RUNNER_ACCESS_ROLE_ARN=$APPRUNNER_ROLE_ARN"
echo ""
echo "To add secrets to GitHub:"
echo "1. Go to https://github.com/$GITHUB_ORG/$GITHUB_REPO/settings/secrets/actions"
echo "2. Click 'New repository secret'"
echo "3. Add AWS_ROLE_ARN with value: $GITHUB_ROLE_ARN"
echo "4. Add APP_RUNNER_ACCESS_ROLE_ARN with value: $APPRUNNER_ROLE_ARN"
echo ""
echo "Or use GitHub CLI:"
echo "gh secret set AWS_ROLE_ARN --body \"$GITHUB_ROLE_ARN\""
echo "gh secret set APP_RUNNER_ACCESS_ROLE_ARN --body \"$APPRUNNER_ROLE_ARN\""
echo ""
