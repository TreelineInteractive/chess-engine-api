---
name: Deployment Issue
about: Report a problem with the AWS App Runner deployment
title: '[DEPLOY] '
labels: deployment, infrastructure
assignees: ''
---

## Deployment Issue

**Workflow Run**: [Link to failed workflow run]

**Branch**: main

**Commit SHA**: 

### Problem Description
<!-- Describe what went wrong -->

### Expected Behavior
<!-- What should have happened -->

### Actual Behavior
<!-- What actually happened -->

### Error Messages
<!-- Paste any error messages from GitHub Actions or AWS -->

```
[Paste error messages here]
```

### Steps to Reproduce
1. 
2. 
3. 

### Environment
- **AWS Region**: us-west-2
- **Service Name**: chess-engine-api
- **Domain**: chessengine.treelineint.click

### Checklist
- [ ] GitHub Secrets are set correctly (AWS_ROLE_ARN, APP_RUNNER_ACCESS_ROLE_ARN)
- [ ] OIDC provider exists in AWS account
- [ ] ECR repository exists
- [ ] IAM roles have correct permissions
- [ ] Reviewed GitHub Actions logs
- [ ] Reviewed AWS CloudWatch logs
- [ ] Checked AWS App Runner console

### Additional Context
<!-- Add any other context about the problem here -->

### Deployment Logs
<!-- If available, paste relevant logs -->

<details>
<summary>GitHub Actions Log</summary>

```
[Paste GitHub Actions log here]
```

</details>

<details>
<summary>AWS CloudWatch Log</summary>

```
[Paste CloudWatch log here]
```

</details>

### Attempted Solutions
<!-- What have you tried to fix this? -->

- [ ] Re-ran the workflow
- [ ] Verified secrets
- [ ] Checked AWS console
- [ ] Reviewed documentation
