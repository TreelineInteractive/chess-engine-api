# App Runner Terraform

This Terraform root manages the existing `chess-engine-api` App Runner service in `us-west-2`, plus:

- CloudWatch alarms for `5xxStatusResponses`
- CloudWatch alarms for high `CPUUtilization`
- CloudWatch alarms for high `MemoryUtilization`
- SNS fanout for those alarms
- Optional Slack delivery through SNS -> Lambda -> Slack incoming webhook

## Files

- `main.tf`: App Runner service, alarms, SNS, optional Slack notifier Lambda
- `variables.tf`: Inputs and thresholds
- `terraform.tfvars.example`: Starting point based on the documented app deployment
- `outputs.tf`: Useful ARNs and service metadata

## Selecting the App Runner image

Build and publish the patched engine image using the deployment workflow for the target environment. Before running `terraform plan`, set `TF_VAR_image_identifier` to that image's full ECR URI and commit tag. Terraform also accepts the existing `-var` and local variable-file inputs.

```sh
export TF_VAR_image_identifier="${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com/chess-engine-api:${GIT_COMMIT_SHA}"
```

## Slack Notes

Slack delivery uses an incoming webhook and a small Lambda function.

Set:

```hcl
slack_webhook_url = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
```

When this value is set, Terraform creates:

- a Lambda function named `${service_name}-slack-notifier`
- an SNS subscription from the alerts topic to that Lambda
- Lambda permission allowing SNS to invoke it

The Lambda posts alarm state changes to Slack with the alarm name, reason, new state, region, and a link to the CloudWatch alarm.
