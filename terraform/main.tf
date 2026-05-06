provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

data "aws_iam_policy_document" "alerts_topic" {
  statement {
    sid    = "AllowCloudWatchAlarms"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudwatch.amazonaws.com"]
    }

    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.alerts.arn]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

data "archive_file" "slack_notifier" {
  count = var.slack_webhook_url == null ? 0 : 1

  type        = "zip"
  source_file = "${path.module}/lambda/slack_notifier.py"
  output_path = "${path.module}/.terraform/slack_notifier.zip"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

locals {
  tags = merge(
    {
      ManagedBy = "Terraform"
      Service   = var.service_name
    },
    var.tags
  )

  metric_dimensions = {
    ServiceName                                = aws_apprunner_service.this.service_name
    (var.app_runner_service_id_dimension_name) = aws_apprunner_service.this.service_id
  }
}

resource "aws_apprunner_auto_scaling_configuration_version" "this" {
  count = var.create_auto_scaling_configuration ? 1 : 0

  auto_scaling_configuration_name = var.auto_scaling_configuration_name
  max_concurrency                 = var.auto_scaling_max_concurrency
  max_size                        = var.auto_scaling_max_size
  min_size                        = var.auto_scaling_min_size

  tags = local.tags
}

resource "aws_apprunner_service" "this" {
  service_name = var.service_name

  auto_scaling_configuration_arn = var.create_auto_scaling_configuration ? aws_apprunner_auto_scaling_configuration_version.this[0].arn : var.auto_scaling_configuration_arn

  source_configuration {
    auto_deployments_enabled = var.auto_deployments_enabled

    authentication_configuration {
      access_role_arn = var.ecr_access_role_arn
    }

    image_repository {
      image_identifier      = var.image_identifier
      image_repository_type = var.image_repository_type

      image_configuration {
        port                          = tostring(var.container_port)
        runtime_environment_variables = var.runtime_environment_variables
        runtime_environment_secrets   = var.runtime_environment_secrets
        start_command                 = var.start_command
      }
    }
  }

  instance_configuration {
    cpu               = var.instance_cpu
    memory            = var.instance_memory
    instance_role_arn = var.instance_role_arn
  }

  health_check_configuration {
    protocol            = var.health_check_protocol
    path                = var.health_check_path
    interval            = var.health_check_interval_seconds
    timeout             = var.health_check_timeout_seconds
    healthy_threshold   = var.health_check_healthy_threshold
    unhealthy_threshold = var.health_check_unhealthy_threshold
  }

  network_configuration {
    ingress_configuration {
      is_publicly_accessible = var.is_publicly_accessible
    }

    egress_configuration {
      egress_type       = var.vpc_connector_arn == null ? "DEFAULT" : "VPC"
      vpc_connector_arn = var.vpc_connector_arn
    }
  }

  tags = local.tags

  lifecycle {
    ignore_changes = [observability_configuration]
  }
}

resource "aws_sns_topic" "alerts" {
  name = "${var.service_name}-alerts"
  tags = local.tags
}

resource "aws_sns_topic_policy" "alerts" {
  arn    = aws_sns_topic.alerts.arn
  policy = data.aws_iam_policy_document.alerts_topic.json
}

resource "aws_iam_role" "chatbot" {
  count = var.slack_webhook_url == null ? 0 : 1

  name               = "${var.service_name}-slack-notifier-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
  tags               = local.tags
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  count = var.slack_webhook_url == null ? 0 : 1

  role       = aws_iam_role.chatbot[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "slack_notifier" {
  count = var.slack_webhook_url == null ? 0 : 1

  function_name = "${var.service_name}-slack-notifier"
  role          = aws_iam_role.chatbot[0].arn
  handler       = "slack_notifier.handler"
  runtime       = "python3.13"
  timeout       = 10

  filename         = data.archive_file.slack_notifier[0].output_path
  source_code_hash = data.archive_file.slack_notifier[0].output_base64sha256

  environment {
    variables = {
      SLACK_WEBHOOK_URL = var.slack_webhook_url
    }
  }

  tags = local.tags
}

resource "aws_sns_topic_subscription" "slack_notifier" {
  count = var.slack_webhook_url == null ? 0 : 1

  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.slack_notifier[0].arn
}

resource "aws_lambda_permission" "allow_sns" {
  count = var.slack_webhook_url == null ? 0 : 1

  statement_id  = "AllowExecutionFromSns"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.slack_notifier[0].function_name
  principal     = "sns.amazonaws.com"
  source_arn    = aws_sns_topic.alerts.arn
}

resource "aws_cloudwatch_metric_alarm" "http_5xx" {
  alarm_name          = "${var.service_name}-5xx"
  alarm_description   = "App Runner ${var.service_name} is returning 5xx responses."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.five_xx_evaluation_periods
  metric_name         = "5xxStatusResponses"
  namespace           = "AWS/AppRunner"
  period              = var.five_xx_period_seconds
  statistic           = "Sum"
  threshold           = var.five_xx_threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  dimensions          = local.metric_dimensions

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "cpu_high" {
  alarm_name          = "${var.service_name}-cpu-high"
  alarm_description   = "App Runner ${var.service_name} CPU utilization is high."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.cpu_evaluation_periods
  datapoints_to_alarm = var.cpu_datapoints_to_alarm
  metric_name         = "CPUUtilization"
  namespace           = "AWS/AppRunner"
  period              = var.cpu_period_seconds
  statistic           = "Average"
  threshold           = var.cpu_threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  dimensions          = local.metric_dimensions

  tags = local.tags
}

resource "aws_cloudwatch_metric_alarm" "memory_high" {
  alarm_name          = "${var.service_name}-memory-high"
  alarm_description   = "App Runner ${var.service_name} memory utilization is high."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = var.memory_evaluation_periods
  datapoints_to_alarm = var.memory_datapoints_to_alarm
  metric_name         = "MemoryUtilization"
  namespace           = "AWS/AppRunner"
  period              = var.memory_period_seconds
  statistic           = "Average"
  threshold           = var.memory_threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
  dimensions          = local.metric_dimensions

  tags = local.tags
}
