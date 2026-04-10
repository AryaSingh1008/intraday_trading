# ─────────────────────────────────────────────────────────────────────────────
# EventBridge Scheduler — replaces the Playwright 150s background loop
# All schedules are in UTC. Indian market is UTC+5:30.
# Market hours: 9:15–15:30 IST = 3:45–10:00 UTC
# ─────────────────────────────────────────────────────────────────────────────

# Scheduler Group (logical container for all trading schedules)
resource "aws_scheduler_schedule_group" "trading" {
  name = "${local.prefix}-schedules"
}

# ── Rule 1: Options cache refresh — DISABLED (caching removed) ─────────────
# Cache pre-warming is no longer needed — all analysis uses live data.
# Kept commented out for reference.
# resource "aws_scheduler_schedule" "options_refresh" { ... }

# ── Rule 2: Stock signal pre-warming — DISABLED (caching removed) ──────────
# Cache pre-warming is no longer needed — all analysis uses live data.
# Kept commented out for reference.
# resource "aws_scheduler_schedule" "stocks_refresh" { ... }

# ── Rule 3: Daily IV history append — after market close ───────────────────
# Runs at 15:40 IST (10:10 UTC) on trading days to record the day's ATM IV
resource "aws_scheduler_schedule" "iv_history_append" {
  name       = "${local.prefix}-iv-history-append"
  group_name = aws_scheduler_schedule_group.trading.name

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 10   # Allow up to 10-min drift — IV data doesn't need precision
  }

  # 15:40 IST = 10:10 UTC, weekdays only
  schedule_expression          = "cron(40 15 ? * MON-FRI *)"
  schedule_expression_timezone = "Asia/Kolkata"

  target {
    arn      = aws_lambda_function.options_refresh.arn
    role_arn = aws_iam_role.scheduler_exec.arn

    input = jsonencode({
      source = "eventbridge"
      type   = "iv_history_append"
    })

    retry_policy {
      maximum_retry_attempts       = 2
      maximum_event_age_in_seconds = 600
    }
  }
}
