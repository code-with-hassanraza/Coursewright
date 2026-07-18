# Coursewright — AWS Infrastructure Registry
**Region:** us-east-1
**Account ID:** 79********10
**Owner:** Muhammad Hassan Raza (Team Lead)

This file is the single source of truth for every AWS resource in the
Coursewright infrastructure. Real ARNs, endpoints, and credentials are
stored in your local private notes file — never in this file.

---

## Build Status

| Step | Resource | Status |
|------|----------|--------|
| 8 | IAM — EC2 Role + GitHub OIDC Role | ✅ Done |
| 9 | Security Groups — EC2 + RDS | ✅ Done |
| 10 | RDS PostgreSQL (private) | ✅ Done |
| 11 | Secrets Manager | ✅ Done |
| 12 | S3 Bucket (frontend) | ⬜ Pending |
| 13 | CloudFront + ACM Certificate | ⬜ Pending |
| 14 | ECR Repository | ⬜ Pending |
| 15 | EC2 Instance + Elastic IP | ⬜ Pending |
| 16 | Nginx + SSL (Certbot) | ⬜ Pending |
| 17 | GuardDuty + CloudTrail | ⬜ Pending |

---

## Step 8 — IAM ✅

### EC2 Instance Role
Allows the EC2 instance to pull secrets, write logs, and pull Docker images.
Uses temporary credentials auto-rotated every hour — no long-lived keys on instance.

| Resource | Value |
|----------|-------|
| Role Name | `coursewright-ec2-role` |
| Role ARN | `arn:aws:iam::79********10:role/coursewright-ec2-role` |
| Policy Name | `coursewright-ec2-policy` |
| Policy ARN | `arn:aws:iam::79********10:policy/coursewright-ec2-policy` |
| Instance Profile Name | `coursewright-ec2-profile` |
| Instance Profile ARN | `arn:aws:iam::79********10:instance-profile/coursewright-ec2-profile` |
| Created | 2026-07-16 |

**Permissions granted:**
- `secretsmanager:GetSecretValue` → scoped to `arn:...:secret:coursewright/*`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` → scoped to `/coursewright/*`
- `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:BatchCheckLayerAvailability` → scoped to `coursewright-backend` repo
- `ecr:GetAuthorizationToken` → `*` (AWS requirement)

**Policy files:** `infra/aws/iam/ec2-trust-policy.json`, `infra/aws/iam/ec2-permission-policy.json`

---

### GitHub Actions OIDC Role
Allows GitHub Actions CI/CD to deploy frontend and backend.
Uses OIDC — no long-lived access keys stored anywhere.

| Resource | Value |
|----------|-------|
| Role Name | `coursewright-github-actions-role` |
| Role ARN | `arn:aws:iam::79********10:role/coursewright-github-actions-role` |
| Policy Name | `coursewright-github-actions-policy` |
| Policy ARN | `arn:aws:iam::79********10:policy/coursewright-github-actions-policy` |
| OIDC Provider | `token.actions.githubusercontent.com` |
| Trust Condition | `repo:code-with-hassanraza/Coursewright:ref:refs/heads/main` |
| Created | 2026-07-16 |

**Permissions granted:**
- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` → scoped to `coursewright-frontend-prod`
- `cloudfront:CreateInvalidation` → `*` (AWS requirement)
- ECR push permissions → scoped to `coursewright-backend` repo
- `ecr:GetAuthorizationToken` → `*` (AWS requirement)

**Policy files:** `infra/aws/iam/github-trust-policy.json`, `infra/aws/iam/github-permission-policy.json`

---

## Step 9 — Security Groups ✅

### EC2 Security Group

| Resource | Value |
|----------|-------|
| Group Name | `coursewright-ec2-sg` |
| Group ID | `sg-093f****e84060` |
| VPC | `vpc-0b50****863286` (default VPC) |
| Created | 2026-07-17 |

**Inbound rules:**
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 80 | TCP | 0.0.0.0/0 | HTTP — Nginx redirects to HTTPS |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 22 | TCP | Owner IP/32 | SSH — locked to owner IP only |

**Note:** SSH rule must be updated when owner dynamic IP changes.

---

### RDS Security Group

| Resource | Value |
|----------|-------|
| Group Name | `coursewright-rds-sg` |
| Group ID | `sg-05c5****ab95c1` |
| VPC | `vpc-0b50****863286` (default VPC) |
| Created | 2026-07-17 |

**Inbound rules:**
| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 5432 | TCP | `sg-093f****e84060` (EC2 SG) | PostgreSQL — EC2 only, never public |

---

## Step 10 — RDS PostgreSQL ✅

| Resource | Value |
|----------|-------|
| DB Identifier | `coursewright-prod` |
| DB Name | `coursewright` |
| Master Username | `cw_user` |
| Engine | PostgreSQL 15.x |
| Instance Class | `db.t3.micro` |
| Storage | 20 GB gp2 |
| Endpoint | See private notes |
| Port | 5432 |
| Publicly Accessible | **NO** |
| Multi-AZ | No |
| Backup Retention | 7 days |
| Subnet Group | `coursewright-subnet-group` (all 6 us-east-1 AZs) |
| Security Group | `coursewright-rds-sg` |
| Created | 2026-07-17 |

**Security:** No public IP assigned. Only resources attached to
`coursewright-ec2-sg` can reach port 5432.

---

## Step 11 — Secrets Manager ✅

| Resource | Value |
|----------|-------|
| Secret Name | `coursewright/prod/app-secrets` |
| Secret ARN | See private notes |
| KMS Key | AWS managed (`aws/secretsmanager`) |
| Region | us-east-1 |
| Created | 2026-07-17 |

**Keys stored (6 total):**
| Key | Status |
|-----|--------|
| `DATABASE_URL` | ✅ Set — points to RDS endpoint |
| `SECRET_KEY` | ✅ Set — 32-byte hex, JWT signing |
| `ENVIRONMENT` | ✅ Set — `production` |
| `ALLOWED_ORIGINS` | ⏳ Placeholder — update after Step 13 (CloudFront) |
| `GEMINI_API_KEY` | ⏳ Placeholder — add key before go-live |
| `GROQ_API_KEY` | ⏳ Placeholder — add key before go-live |

**Template file:** `infra/aws/secrets.example.json`
**Real file:** `infra/aws/secrets.json` (local only, in .gitignore)

**How EC2 reads these at startup:**
EC2 user data script fetches this secret using `coursewright-ec2-role`
and writes values to `/home/ubuntu/.env`. No credentials stored on disk permanently.

---

## Step 12 — S3 Bucket (Frontend) ⬜

| Resource | Value |
|----------|-------|
| Bucket Name | `coursewright-frontend-prod` |
| Bucket ARN | FILL AFTER CREATION |
| Region | us-east-1 |
| Public Access | Blocked — CloudFront OAC only |
| Versioning | Enabled |
| Created | FILL AFTER CREATION |

---

## Step 13 — CloudFront + ACM ⬜

### ACM Certificate
| Resource | Value |
|----------|-------|
| Domain | FILL WITH YOUR DOMAIN |
| Certificate ARN | FILL AFTER CREATION |
| Region | us-east-1 (required for CloudFront) |

### CloudFront Distribution
| Resource | Value |
|----------|-------|
| Distribution ID | FILL AFTER CREATION |
| Domain Name | FILL AFTER CREATION.cloudfront.net |
| Origin | S3 bucket via OAC |
| Default Root Object | `index.html` |
| HTTPS | Redirect HTTP to HTTPS |
| Created | FILL AFTER CREATION |

---

## Step 14 — ECR Repository ⬜

| Resource | Value |
|----------|-------|
| Repository Name | `coursewright-backend` |
| Repository URI | `79********10.dkr.ecr.us-east-1.amazonaws.com/coursewright-backend` |
| Repository ARN | FILL AFTER CREATION |
| Image Tag Mutability | MUTABLE |
| Scan on Push | Enabled |
| Created | FILL AFTER CREATION |

---

## Step 15 — EC2 Instance ⬜

| Resource | Value |
|----------|-------|
| Instance ID | FILL AFTER CREATION |
| AMI | Ubuntu 22.04 LTS |
| Instance Type | `t3.small` |
| IAM Profile | `coursewright-ec2-profile` |
| Security Group | `coursewright-ec2-sg` |
| Elastic IP | FILL AFTER CREATION |
| Key Pair Name | FILL AFTER CREATION |
| Created | FILL AFTER CREATION |

---

## Step 16 — Nginx + SSL ⬜

| Resource | Value |
|----------|-------|
| Domain | FILL WITH YOUR DOMAIN |
| SSL Certificate | Let's Encrypt via Certbot |
| Nginx Config | `/etc/nginx/sites-available/coursewright` |
| Status | ⬜ Pending |

---

## Step 17 — Security Monitoring ⬜

### GuardDuty
| Resource | Value |
|----------|-------|
| Detector ID | FILL AFTER CREATION |
| Alert Threshold | Severity >= 7 (HIGH) |
| Status | ⬜ Pending |

### CloudTrail
| Resource | Value |
|----------|-------|
| Trail Name | `coursewright-trail` |
| S3 Bucket | `coursewright-cloudtrail-logs` |
| Multi-Region | Yes |
| Log Validation | Enabled |
| Status | ⬜ Pending |

### CloudWatch
| Resource | Value |
|----------|-------|
| Log Group | `/coursewright/backend` |
| Status | ⬜ Pending |

### SNS (GuardDuty Alerts)
| Resource | Value |
|----------|-------|
| Topic Name | `coursewright-security-alerts` |
| Topic ARN | FILL AFTER CREATION |
| Subscription | Email alert on HIGH severity findings |
| Status | ⬜ Pending |

---

## GitHub Actions Secrets

GitHub → Coursewright repo → Settings → Secrets and variables → Actions

| Secret Name | Value | Available |
|-------------|-------|-----------|
| `AWS_ROLE_ARN` | `arn:aws:iam::79********10:role/coursewright-github-actions-role` | ✅ Now |
| `S3_BUCKET_NAME` | `coursewright-frontend-prod` | Step 12 |
| `CF_DISTRIBUTION_ID` | CloudFront distribution ID | Step 13 |
| `ECR_REPOSITORY_URI` | `79********10.dkr.ecr.us-east-1.amazonaws.com/coursewright-backend` | Step 14 |
| `EC2_HOST` | Elastic IP | Step 15 |
| `EC2_SSH_KEY` | Full private key content | Step 15 |
| `VITE_API_URL` | `https://yourdomain.com/api/v1` | Step 16 |

---

## Quick Reference — Resource Names

| Resource | Name / Identifier |
|----------|-------------------|
| EC2 Role | `coursewright-ec2-role` |
| EC2 Instance Profile | `coursewright-ec2-profile` |
| GitHub Actions Role | `coursewright-github-actions-role` |
| EC2 Security Group | `coursewright-ec2-sg` |
| RDS Security Group | `coursewright-rds-sg` |
| RDS Instance | `coursewright-prod` |
| DB Subnet Group | `coursewright-subnet-group` |
| Secret | `coursewright/prod/app-secrets` |
| S3 Bucket | `coursewright-frontend-prod` |
| ECR Repo | `coursewright-backend` |
| CloudTrail Bucket | `coursewright-cloudtrail-logs` |
| CloudWatch Log Group | `/coursewright/backend` |
| SNS Topic | `coursewright-security-alerts` |

*All real ARNs, endpoints, and credentials are in your local private notes file.*