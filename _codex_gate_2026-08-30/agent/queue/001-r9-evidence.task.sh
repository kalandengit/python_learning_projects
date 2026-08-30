# R9 post-run evidence collection. Read-only.
D=/var/backups/kalanfa-gate-r7c8g-r3-r2-r2-stage08-overlay2-portable-identity-immutability-fix/20260830T050531Z
D8=/var/backups/kalanfa-gate-r7c8g-r3-r2-r2-stage08-overlay2-portable-identity-immutability-fix/20260830T040529Z

echo "===== 1. evidence files ====="
ls -l "$D" 2>&1

echo "===== 2. did the R9 block run? ====="
grep -c 'R9_RENDERED_COMPOSE_DIAGNOSTICS' "$D/runtime_certification.log" 2>/dev/null \
  || echo "NO_FILE_OR_NO_MATCH"

echo "===== 3. the R9 diagnostic block ====="
sed -n '/R9_RENDERED_COMPOSE_DIAGNOSTICS_BEGIN/,/R9_RENDERED_COMPOSE_DIAGNOSTICS_END/p' \
  "$D/runtime_certification.log" 2>/dev/null

echo "===== 4. where the runtime stage died ====="
tail -80 "$D/runtime_certification.log" 2>/dev/null

echo "===== 5. R8 vs R9 marker divergence ====="
diff <(grep -oE '^[A-Z0-9_]+=' "$D8/runtime_certification.log" 2>/dev/null) \
     <(grep -oE '^[A-Z0-9_]+='  "$D/runtime_certification.log" 2>/dev/null) | head -40

echo "===== 6. status ====="
cat "$D/STATUS.txt" 2>/dev/null

echo "===== 7. runner identity ====="
sha256sum /root/R7C8G_R3_R2_R9.sh /root/R7C8G_R3_R2_R8.sh 2>&1
