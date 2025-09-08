#!/bin/bash

# Set default export filename and environment
EXPORT_FILE="survey_export.csv"
ENVIRONMENT="prod"

# Parse command line arguments
while getopts "o:e:" opt; do
  case $opt in
    o)
      EXPORT_FILE="$OPTARG"
      ;;
    e)
      ENVIRONMENT="$OPTARG"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
  esac
done

# Validate environment
if [[ "$ENVIRONMENT" != "prod" && "$ENVIRONMENT" != "dev" ]]; then
  echo "Invalid environment: $ENVIRONMENT. Must be 'prod' or 'dev'" >&2
  exit 1
fi

docker compose exec -T -u root survey-flask-$ENVIRONMENT sqlite3 /tmp/dev.db <<EOF
.headers on
.mode csv
.output /app/${EXPORT_FILE}
SELECT
  u.id              AS user_id,
  u.participant_id,
  utp.test_type,
  utp.condition_number,
  utp.choices,
  utp.response_times,
  ir.mental_demand,
  ir.success_level,
  ir.frustration_level,
  ir.trajectory_choice_ease,
  ir.difference_clarity,
  ir.preference_learning,
  ir.decision_factors,
  ir.attention_check_pass,
  ir.created_at
FROM users u
LEFT JOIN user_test_progress utp
  ON u.id = utp.user_id
LEFT JOIN inter_round_survey_responses ir
  ON u.id = ir.user_id
 AND utp.test_type       = ir.test_type
 AND utp.condition_number = ir.condition_number
;
.quit
EOF

echo "Data exported to ${EXPORT_FILE} from ${ENVIRONMENT} environment"