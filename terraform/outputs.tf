output "app_runner_service_arn" {
  description = "App Runner service ARN."
  value       = aws_apprunner_service.this.arn
}

output "app_runner_service_id" {
  description = "App Runner service ID."
  value       = aws_apprunner_service.this.service_id
}

output "app_runner_service_url" {
  description = "App Runner service URL."
  value       = aws_apprunner_service.this.service_url
}

output "alerts_sns_topic_arn" {
  description = "SNS topic used by CloudWatch alarms."
  value       = aws_sns_topic.alerts.arn
}

output "slack_notifier_lambda_arn" {
  description = "Slack notifier Lambda ARN, if enabled."
  value       = try(aws_lambda_function.slack_notifier[0].arn, null)
}
