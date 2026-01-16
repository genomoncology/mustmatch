# DevOps Script Verification

## The Problem

DevOps scripts fail silently:

```bash skip
#!/bin/bash
# deploy.sh

kubectl apply -f service.yaml
curl http://myapp/health  # Returns 500, script continues anyway
kubectl scale deployment myapp --replicas=10
# Deployed broken version to production 🔥
```

**Result:** 3am pages, rollbacks, postmortems.

## The Solution

Self-verifying scripts with mustmatch:

```bash skip
#!/bin/bash
set -e  # Exit on any failure

# Deploy
kubectl apply -f service.yaml | \
    mustmatch like "created" || exit 1

# Verify health
curl -f http://myapp/health | \
    mustmatch '{"status":"healthy"}' || {
    echo "Health check failed, rolling back"
    kubectl rollout undo deployment/myapp
    exit 1
}

# Scale
kubectl scale deployment myapp --replicas=10 | \
    mustmatch like "scaled" || exit 1

echo "✓ Deployment successful"
```

**Result:** Failures caught immediately, automatic rollback.

## Common Use Cases

### 1. Health Checks

```bash skip
#!/bin/bash
# health-check.sh

# Check service is running
systemctl is-active myapp | mustmatch "active" || {
    echo "ERROR: Service is not active"
    exit 1
}

# Check port is listening
ss -tlnp | mustmatch like ":8080" || {
    echo "ERROR: Port 8080 not listening"
    exit 1
}

# Check HTTP responds
curl -f http://localhost:8080/health | \
    mustmatch '{"status":"ok"}' || {
    echo "ERROR: Health endpoint unhealthy"
    exit 1
}

echo "✓ All health checks passed"
```

### 2. Pre-Deployment Validation

```bash skip
#!/bin/bash
# pre-deploy.sh

echo "Running pre-deployment checks..."

# Verify infrastructure
terraform plan | mustmatch "No changes" || {
    echo "ERROR: Unexpected infrastructure drift detected"
    exit 1
}

# Verify database connectivity
psql -h $DB_HOST -U $DB_USER -c "SELECT 1" | \
    mustmatch "1" || {
    echo "ERROR: Cannot connect to database"
    exit 1
}

# Verify disk space
df -h / | mustmatch not like "100%" || {
    echo "ERROR: Disk full"
    exit 1
}

# Verify API dependencies
curl -f https://api.dependency.com/health | \
    mustmatch like '"status":"up"' || {
    echo "WARNING: External API may be down"
    # Don't exit, just warn
}

echo "✓ Pre-deployment checks passed"
```

### 3. Post-Deployment Verification

```bash skip
#!/bin/bash
# post-deploy.sh

echo "Verifying deployment..."

# Wait for pods to be ready
sleep 10

# Check pod status
kubectl get pods -l app=myapp | \
    mustmatch like "Running" || {
    echo "ERROR: Pods not running"
    kubectl describe pods -l app=myapp
    exit 1
}

# Check replica count
kubectl get deployment myapp -o json | \
    mustmatch like '"readyReplicas":3' || {
    echo "ERROR: Expected 3 ready replicas"
    exit 1
}

# Smoke test the API
curl -f https://myapp.production.com/api/version | \
    mustmatch like '"version":"2.0"' || {
    echo "ERROR: Version mismatch"
    exit 1
}

# Test key endpoint
curl -f https://myapp.production.com/api/users | \
    mustmatch like '{"users":[{' || {
    echo "ERROR: Users endpoint broken"
    exit 1
}

echo "✓ Deployment verified"
```

### 4. Configuration Verification

```bash skip
#!/bin/bash
# verify-config.sh

echo "Verifying configuration..."

# Check environment variables
echo $DATABASE_URL | mustmatch like "postgresql://" || {
    echo "ERROR: DATABASE_URL not configured"
    exit 1
}

# Check config file exists and has correct format
cat /etc/myapp/config.json | \
    mustmatch like '{"database":{"host"' || {
    echo "ERROR: Config file malformed"
    exit 1
}

# Check secrets are loaded
kubectl get secret myapp-secrets -o json | \
    mustmatch like '"api-key"' || {
    echo "ERROR: Secrets not configured"
    exit 1
}

# Verify SSL certificates
openssl x509 -in /etc/ssl/myapp.crt -noout -dates | \
    mustmatch not like "expired" || {
    echo "ERROR: SSL certificate expired"
    exit 1
}

echo "✓ Configuration valid"
```

### 5. Database Migrations

```bash skip
#!/bin/bash
# migrate.sh

echo "Running database migrations..."

# Check current schema version
psql -t -c "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1" | \
    mustmatch "5" || {
    echo "ERROR: Unexpected schema version"
    exit 1
}

# Run migration
./db-migrate up | mustmatch like "Migration successful" || {
    echo "ERROR: Migration failed"
    ./db-migrate down  # Rollback
    exit 1
}

# Verify new schema
psql -t -c "SELECT version FROM schema_version ORDER BY version DESC LIMIT 1" | \
    mustmatch "6" || {
    echo "ERROR: Migration did not update version"
    exit 1
}

# Smoke test
psql -c "SELECT * FROM users LIMIT 1" | \
    mustmatch like "id" || {
    echo "ERROR: Cannot query users table"
    exit 1
}

echo "✓ Migration completed"
```

### 6. Backup Verification

```bash skip
#!/bin/bash
# verify-backup.sh

BACKUP_DATE=$(date +%Y-%m-%d)

echo "Verifying backup for $BACKUP_DATE..."

# Check backup file exists
ls /backups/ | mustmatch like "$BACKUP_DATE" || {
    echo "ERROR: No backup found for today"
    exit 1
}

# Check backup size (should be > 1MB)
du -h /backups/db-$BACKUP_DATE.sql.gz | \
    mustmatch not like "^0" || {
    echo "ERROR: Backup file is empty"
    exit 1
}

# Test restore to temp database
createdb test_restore
gunzip -c /backups/db-$BACKUP_DATE.sql.gz | psql test_restore
psql test_restore -c "SELECT COUNT(*) FROM users" | \
    mustmatch not like "0" || {
    echo "ERROR: Restored database is empty"
    dropdb test_restore
    exit 1
}

dropdb test_restore
echo "✓ Backup verified"
```

### 7. Security Checks

```bash skip
#!/bin/bash
# security-check.sh

echo "Running security checks..."

# Check no services listening on public interfaces
ss -tlnp | mustmatch not like "0.0.0.0:3306" || {
    echo "WARNING: MySQL exposed to public"
}

ss -tlnp | mustmatch not like "0.0.0.0:6379" || {
    echo "WARNING: Redis exposed to public"
}

# Check firewall is active
systemctl is-active firewalld | mustmatch "active" || {
    echo "WARNING: Firewall not active"
}

# Check SSL/TLS settings
curl -I https://myapp.com 2>&1 | \
    mustmatch like "HTTP/2" || {
    echo "WARNING: Not using HTTP/2"
}

# Check for default passwords
grep -r "password" /etc/myapp/ | mustmatch not like "admin123" || {
    echo "ERROR: Default password detected"
    exit 1
}

echo "✓ Security checks passed"
```

### 8. Infrastructure State

```bash skip
#!/bin/bash
# check-infrastructure.sh

echo "Checking infrastructure state..."

# Verify EC2 instances
aws ec2 describe-instances \
    --filters "Name=tag:Environment,Values=production" \
    --query 'Reservations[*].Instances[*].[State.Name]' \
    --output text | \
    mustmatch not like "stopped" || {
    echo "ERROR: Production instances are stopped"
    exit 1
}

# Verify S3 bucket exists
aws s3 ls | mustmatch like "myapp-backups" || {
    echo "ERROR: Backup bucket not found"
    exit 1
}

# Verify RDS is available
aws rds describe-db-instances \
    --db-instance-identifier myapp-prod \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text | \
    mustmatch "available" || {
    echo "ERROR: RDS not available"
    exit 1
}

echo "✓ Infrastructure state verified"
```

## Integration Patterns

### With CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install mustmatch
        run: pip install mustmatch

      - name: Pre-deployment checks
        run: ./scripts/pre-deploy.sh

      - name: Deploy
        run: ./scripts/deploy.sh

      - name: Post-deployment checks
        run: ./scripts/post-deploy.sh

      - name: Verify health
        run: |
          curl https://myapp.com/health | \
            mustmatch '{"status":"healthy"}'
```

### With Monitoring

```bash skip
#!/bin/bash
# monitor.sh - Run every 5 minutes via cron

# Check and report to monitoring system
if curl -s http://localhost:8080/health | mustmatch -q '{"status":"ok"}'; then
    # Send OK to monitoring
    curl -X POST https://monitoring.com/status \
        -d '{"service":"myapp","status":"up"}'
else
    # Send alert
    curl -X POST https://monitoring.com/alert \
        -d '{"service":"myapp","status":"down"}'
fi
```

### With Ansible

```yaml
# playbook.yml
- name: Deploy and verify application
  hosts: production
  tasks:
    - name: Deploy application
      shell: kubectl apply -f /tmp/deployment.yaml

    - name: Wait for rollout
      shell: kubectl rollout status deployment/myapp

    - name: Verify health endpoint
      shell: |
        curl http://localhost:8080/health | \
          mustmatch '{"status":"ok"}'
      register: health_check
      failed_when: health_check.rc != 0

    - name: Verify API
      shell: |
        curl http://localhost:8080/api/version | \
          mustmatch like '"version"'
      register: api_check
      failed_when: api_check.rc != 0
```

## Best Practices

### 1. Always Set -e

```bash
#!/bin/bash
set -e  # Exit on any error
set -o pipefail  # Catch errors in pipes

# Now any failure stops the script
```

### 2. Provide Clear Error Messages

```bash skip
# Good
curl http://api.com | mustmatch '{"status":"ok"}' || {
    echo "ERROR: API health check failed"
    echo "Expected: {\"status\":\"ok\"}"
    echo "Try: curl http://api.com"
    exit 1
}

# Bad
curl http://api.com | mustmatch '{"status":"ok"}'
```

### 3. Use Timeouts

```bash skip
# Add timeout to prevent hanging
timeout 10 curl http://api.com | mustmatch '{"status":"ok"}' || {
    echo "ERROR: Health check timed out after 10s"
    exit 1
}
```

### 4. Test Your Tests

```bash skip
# Document expected behavior
cat > test-health-check.md << 'EOF'
# Health Check Tests

Should pass when healthy:

```bash
echo '{"status":"ok"}' | mustmatch '{"status":"ok"}'
```

Should fail when unhealthy:

```bash
echo '{"status":"error"}' | mustmatch not '{"status":"ok"}'
```
EOF

mustmatch test test-health-check.md
```

### 5. Combine with Logging

```bash skip
#!/bin/bash
LOG_FILE="/var/log/deploy-$(date +%Y%m%d-%H%M%S).log"

{
    echo "=== Deployment started at $(date) ==="

    if curl http://localhost:8080/health | mustmatch '{"status":"ok"}'; then
        echo "✓ Health check passed"
    else
        echo "✗ Health check failed"
        exit 1
    fi

    echo "=== Deployment completed at $(date) ==="
} | tee -a "$LOG_FILE"
```

## Troubleshooting

### Issue: Intermittent Failures

```bash skip
# Retry with backoff
for i in {1..5}; do
    if curl http://api.com | mustmatch -q '{"status":"ok"}'; then
        echo "✓ Health check passed"
        exit 0
    fi
    echo "Attempt $i failed, retrying in ${i}s..."
    sleep $i
done

echo "✗ Health check failed after 5 attempts"
exit 1
```

### Issue: Need Debugging Output

```bash skip
# Capture output for debugging
OUTPUT=$(curl http://api.com)
echo "API returned: $OUTPUT"

if echo "$OUTPUT" | mustmatch '{"status":"ok"}'; then
    echo "✓ Health check passed"
else
    echo "✗ Health check failed"
    echo "Expected: {\"status\":\"ok\"}"
    echo "Got: $OUTPUT"
    exit 1
fi
```

### Issue: Complex Validation

```bash skip
# Use multiple checks
curl http://api.com/status | {
    read STATUS
    echo "$STATUS" | mustmatch like '"status":"ok"' || exit 1
    echo "$STATUS" | mustmatch like '"uptime"' || exit 1
    echo "$STATUS" | mustmatch not like '"errors"' || exit 1
    echo "✓ All status checks passed"
}
```

## Summary

mustmatch transforms DevOps scripts from "hope it works" to "prove it works":

- **Health checks** that actually verify health
- **Deployments** that roll back on failure
- **Configurations** that are validated
- **Migrations** that are smoke-tested
- **Backups** that are verified restorable

Your infrastructure scripts become self-documenting and self-verifying.
