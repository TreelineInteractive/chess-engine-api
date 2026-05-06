aws_region          = "us-west-2"
service_name        = "chess-engine-api"
image_identifier    = "022911965477.dkr.ecr.us-west-2.amazonaws.com/chess-engine-api:3c65a0f7fc4c982528d3ae67872acdbd44d086b6"
ecr_access_role_arn = "arn:aws:iam::022911965477:role/service-role/AppRunnerECRAccessRole"

instance_cpu    = "1024"
instance_memory = "2048"

create_auto_scaling_configuration = false
auto_scaling_configuration_name   = "chess-engine-api"
auto_scaling_max_concurrency      = 10
auto_scaling_max_size             = 5
auto_scaling_min_size             = 1

health_check_path = "/api/v1/health"

runtime_environment_variables = {
  API_RATE_LIMIT_PER_MINUTE = "100"
  API_VERSION               = "1.2.0"
  AUTH_ENABLED              = "false"
  CORS_ORIGINS              = "*"
  DEBUG                     = "false"
  DEFAULT_DEPTH             = "15"
  HOST                      = "0.0.0.0"
  JWKS_URL                  = "https://ejlvibtuzkrdzpyfnfkp.supabase.co/auth/v1/.well-known/jwks.json"
  JWT_AUDIENCE              = "authenticated"
  LOG_FORMAT                = "json"
  LOG_LEVEL                 = "INFO"
  MAX_ANALYSIS_TIME_MS      = "10000"
  MAX_CONCURRENT_ANALYSES   = "10"
  MAX_DEPTH                 = "25"
  MAX_MULTI_PV              = "5"
  PORT                      = "8000"
  STOCKFISH_HASH_SIZE_MB    = "256"
  STOCKFISH_PATH            = "/usr/local/bin/stockfish"
  STOCKFISH_SKILL_LEVEL     = "20"
  STOCKFISH_THREADS         = "2"
}

runtime_environment_secrets = {
}

five_xx_threshold = 1
cpu_threshold     = 80
memory_threshold  = 80

slack_webhook_url = "https://hooks.slack.com/services/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"

tags = {
  Environment = "production"
}
