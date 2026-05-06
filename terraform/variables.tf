variable "aws_region" {
  description = "AWS region for the App Runner service."
  type        = string
  default     = "us-west-2"
}

variable "service_name" {
  description = "App Runner service name."
  type        = string
  default     = "chess-engine-api"
}

variable "image_identifier" {
  description = "Full ECR image identifier, for example 123456789012.dkr.ecr.us-west-2.amazonaws.com/chess-engine-api:latest."
  type        = string
}

variable "image_repository_type" {
  description = "App Runner image repository type."
  type        = string
  default     = "ECR"
}

variable "ecr_access_role_arn" {
  description = "IAM role ARN that lets App Runner pull from private ECR."
  type        = string
}

variable "auto_deployments_enabled" {
  description = "Whether App Runner should redeploy automatically when the source image changes."
  type        = bool
  default     = false
}

variable "container_port" {
  description = "Port exposed by the container."
  type        = number
  default     = 8000
}

variable "start_command" {
  description = "Optional container start command override."
  type        = string
  default     = null
  nullable    = true
}

variable "runtime_environment_variables" {
  description = "Plaintext runtime environment variables for the service."
  type        = map(string)
  default     = {}
}

variable "runtime_environment_secrets" {
  description = "Runtime secrets for the service. Values should be Secrets Manager or SSM ARNs/names supported by App Runner."
  type        = map(string)
  default     = {}
}

variable "instance_cpu" {
  description = "App Runner instance CPU setting. For imported services, use the raw App Runner value such as 1024."
  type        = string
  default     = "1024"
}

variable "instance_memory" {
  description = "App Runner instance memory setting. For imported services, use the raw App Runner value such as 2048 or 4096."
  type        = string
  default     = "4096"
}

variable "instance_role_arn" {
  description = "Optional App Runner instance role ARN, typically only needed when the app reads AWS services directly."
  type        = string
  default     = null
  nullable    = true
}

variable "health_check_protocol" {
  description = "App Runner health check protocol."
  type        = string
  default     = "HTTP"
}

variable "health_check_path" {
  description = "App Runner health check path."
  type        = string
  default     = "/api/v1/health"
}

variable "health_check_interval_seconds" {
  description = "Health check interval in seconds."
  type        = number
  default     = 10
}

variable "health_check_timeout_seconds" {
  description = "Health check timeout in seconds."
  type        = number
  default     = 5
}

variable "health_check_healthy_threshold" {
  description = "Healthy threshold for App Runner health checks."
  type        = number
  default     = 1
}

variable "health_check_unhealthy_threshold" {
  description = "Unhealthy threshold for App Runner health checks."
  type        = number
  default     = 5
}

variable "is_publicly_accessible" {
  description = "Whether the App Runner service should be publicly accessible."
  type        = bool
  default     = true
}

variable "vpc_connector_arn" {
  description = "Optional App Runner VPC connector ARN for outbound traffic."
  type        = string
  default     = null
  nullable    = true
}

variable "create_auto_scaling_configuration" {
  description = "Create and attach a dedicated App Runner auto scaling configuration."
  type        = bool
  default     = true
}

variable "auto_scaling_configuration_arn" {
  description = "Existing App Runner auto scaling configuration ARN to use when create_auto_scaling_configuration is false."
  type        = string
  default     = null
  nullable    = true
}

variable "auto_scaling_configuration_name" {
  description = "Name for the dedicated App Runner auto scaling configuration."
  type        = string
  default     = "chess-engine-api"
}

variable "auto_scaling_max_concurrency" {
  description = "Maximum requests per instance before App Runner scales out."
  type        = number
  default     = 10
}

variable "auto_scaling_max_size" {
  description = "Maximum number of active App Runner instances."
  type        = number
  default     = 5
}

variable "auto_scaling_min_size" {
  description = "Minimum number of active App Runner instances."
  type        = number
  default     = 1
}

variable "app_runner_service_id_dimension_name" {
  description = "CloudWatch dimension name for the App Runner service ID. ServiceID is the common value; switch to ServiceId if your account exposes that variant."
  type        = string
  default     = "ServiceID"
}

variable "five_xx_threshold" {
  description = "Alarm threshold for App Runner 5xx responses over the configured period."
  type        = number
  default     = 5
}

variable "five_xx_period_seconds" {
  description = "Period for the 5xx alarm."
  type        = number
  default     = 300
}

variable "five_xx_evaluation_periods" {
  description = "Evaluation periods for the 5xx alarm."
  type        = number
  default     = 1
}

variable "cpu_threshold" {
  description = "CPU utilization percentage alarm threshold."
  type        = number
  default     = 80
}

variable "cpu_period_seconds" {
  description = "Period for the CPU utilization alarm."
  type        = number
  default     = 60
}

variable "cpu_evaluation_periods" {
  description = "Evaluation periods for the CPU utilization alarm."
  type        = number
  default     = 5
}

variable "cpu_datapoints_to_alarm" {
  description = "Breaching datapoints required for the CPU utilization alarm."
  type        = number
  default     = 3
}

variable "memory_threshold" {
  description = "Memory utilization percentage alarm threshold."
  type        = number
  default     = 80
}

variable "memory_period_seconds" {
  description = "Period for the memory utilization alarm."
  type        = number
  default     = 60
}

variable "memory_evaluation_periods" {
  description = "Evaluation periods for the memory utilization alarm."
  type        = number
  default     = 5
}

variable "memory_datapoints_to_alarm" {
  description = "Breaching datapoints required for the memory utilization alarm."
  type        = number
  default     = 3
}

variable "slack_webhook_url" {
  description = "Optional Slack incoming webhook URL. When set, SNS alerts are forwarded to Slack through Lambda."
  type        = string
  default     = null
  nullable    = true
  sensitive   = true
}

variable "tags" {
  description = "Additional tags applied to created resources."
  type        = map(string)
  default     = {}
}
