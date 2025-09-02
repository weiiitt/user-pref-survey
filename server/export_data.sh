docker compose exec -T -u root survey-flask-prod sqlite3 /tmp/dev.db <<EOF
.headers on
.mode csv
.output /app/survey_export.csv
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

echo "Data exported to survey_export.csv"