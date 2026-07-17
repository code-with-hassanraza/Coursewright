# Coursewright — AWS Infrastructure Registry
**Region:** us-east-1
**Account ID:** YOUR_ACCOUNT_ID
**Owner:** Muhammad Hassan Raza (Team Lead)

This file is the single source of truth for every AWS resource in the Coursewright
infrastructure. Update it immediately after creating each resource.
Never look up an ARN or ID from the console — it should always be here.

---

## Build Status

| Step | Resource | Status |
|------|----------|--------|
| 8 | IAM — EC2 Role + GitHub OIDC Role | ✅ Done |
| 9 | Security Groups — EC2 + RDS | ⬜ Pending |
| 10 | RDS PostgreSQL (private) | ⬜ Pending |
| 11 | Secrets Manager | ⬜ Pending |
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
No long-lived credentials on the instance — temporary credentials auto-rotate every hour.

| Resource | Value |
|----------|-------|
| Role Name | `coursewright-ec2-role` |
| Role ARN | `arn:aws:iam::YOUR_ACCOUNT_ID:role/coursewright-ec2-role` |
| Policy Name | `coursewright-ec2-policy` |
| Policy ARN | `arn:aws:iam::YOUR_ACCOUNT_ID:policy/coursewright-ec2-policy` |
| Instance Profile Name | `coursewright-ec2-profile` |
| Instance Profile ARN | `arn:aws:iam::YOUR_ACCOUNT_ID:instance-profile/coursewright-ec2-profile` |
| Created | 2026-07-16 |

**Permissions granted:**
- `secretsmanager:GetSecretValue` → scoped to `arn:...:secret:coursewright/*`
- `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents` → scoped to `/coursewright/*`
- `ecr:GetDownloadUrlForLayer`, `ecr:BatchGetImage`, `ecr:BatchCheckLayerAvailability` → scoped to `coursewright-backend` repo
- `ecr:GetAuthorizationToken` → `*` (AWS requirement, cannot scope to a resource)

**Policy files:** `infra/aws/iam/ec2-trust-policy.json`, `infra/aws/iam/ec2-permission-policy.json`

---

### GitHub Actions OIDC Role
Allows GitHub Actions CI/CD to deploy to S3, invalidate CloudFront, and push images to ECR.
Uses OIDC — no long-lived access keys stored in GitHub Secrets.

| Resource | Value |
|----------|-------|
| Role Name | `coursewright-github-actions-role` |
| Role ARN | `arn:aws:iam::YOUR_ACCOUNT_ID:role/coursewright-github-actions-role` |
| Policy Name | `coursewright-github-actions-policy` |
| Policy ARN | `arn:aws:iam::YOUR_ACCOUNT_ID:policy/coursewright-github-actions-policy` |
| OIDC Provider | `token.actions.githubusercontent.com` |
| Trust Condition | `repo:code-with-hassanraza/Coursewright:ref:refs/heads/main` |
| Created | 2026-07-16 |

**Permissions granted:**
- `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket` → scoped to `coursewright-frontend-prod` bucket
- `cloudfront:CreateInvalidation` → `*` (AWS requirement, cannot scope to a resource)
- `ecr:BatchCheckLayerAvailability`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`, `ecr:PutImage` → scoped to `coursewright-backend` repo
- `ecr:GetAuthorizationToken` → `*` (AWS requirement, cannot scope to a resource)

**Policy files:** `infra/aws/iam/github-trust-policy.json`, `infra/aws/iam/github-permission-policy.json`

---

## Step 9 — Security Groups ⬜

### EC2 Security Group

| Resource | Value |
|----------|-------|
| Group Name | `coursewright-ec2-sg` |
| Group ID | `FILL AFTER CREATION` |
| VPC | Default VPC |

**Inbound rules:**
| Port | Protocol | Source | Reason |
|------|----------|--------|--------|
| 80 | TCP | 0.0.0.0/0 | HTTP (redirects to HTTPS via Nginx) |
| 443 | TCP | 0.0.0.0/0 | HTTPS |
| 22 | TCP | YOUR_IP/32 | SSH — your IP only, never open to world |

**Outbound rules:** All traffic allowed (default).

---

### RDS Security Group

| Resource | Value |
|----------|-------|
| Group Name | `coursewright-rds-sg` |
| Group ID | `FILL AFTER CREATION` |
| VPC | Default VPC |

**Inbound rules:**
| Port | Protocol | Source | Reason |
|------|----------|--------|--------|
| 5432 | TCP | coursewright-ec2-sg | Postgres — EC2 only, never public |

---

## Step 10 — RDS PostgreSQL ⬜

| Resource | Value |
|----------|-------|
| DB Identifier | `coursewright-prod` |
| DB Name | `coursewright` |
| Engine | PostgreSQL 15.x |
| Instance Class | `db.t3.micro` |
| Storage | 20 GB gp2 |
| Endpoint | `FILL AFTER CREATION` |
| Port | 5432 |
| Publicly Accessible | **NO** |
| Multi-AZ | No |
| Backup Retention | 7 days |
| Security Group | `coursewright-rds-sg` |
| Created | FILL AFTER CREATION |

---

## Step 11 — Secrets Manager ⬜

| Resource | Value |
|----------|-------|
| Secret Name | `coursewright/prod/app-secrets` |
| Secret ARN | `FILL AFTER CREATION` |
| KMS Key | AWS managed (`aws/secretsmanager`) |
| Region | us-east-1 |
| Created | FILL AFTER CREATION |

**Keys stored:**
- `DATABASE_URL`
- `SECRET_KEY`
- `ENVIRONMENT`
- `ALLOWED_ORIGINS`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`

---

## Step 12 — S3 Bucket (Frontend) ⬜

| Resource | Value |
|----------|-------|
| Bucket Name | `coursewright-frontend-prod` |
| Bucket ARN | `FILL AFTER CREATION` |
| Region | us-east-1 |
| Public Access | Blocked (OAC only) |
| Versioning | Enabled |
| Created | FILL AFTER CREATION |

---

## Step 13 — CloudFront + ACM ⬜

### ACM Certificate

| Resource | Value |
|----------|-------|
| Domain | `FILL WITH YOUR DOMAIN` |
| Certificate ARN | `FILL AFTER CREATION` |
| Region | us-east-1 (required for CloudFront) |
| Status | FILL AFTER CREATION |

### CloudFront Distribution

| Resource | Value |
|----------|-------|
| Distribution ID | `FILL AFTER CREATION` |
| Distribution ARN | `FILL AFTER CREATION` |
| Domain Name | `FILL AFTER CREATION.cloudfront.net` |
| Origin | S3 bucket via OAC |
| Default Root Object | `index.html` |
| HTTPS | Redirect HTTP to HTTPS |
| Created | FILL AFTER CREATION |

---

## Step 14 — ECR Repository ⬜

| Resource | Value |
|----------|-------|
| Repository Name | `coursewright-backend` |
| Repository URI | `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/coursewright-backend` |
| Repository ARN | `FILL AFTER CREATION` |
| Image Tag Mutability | MUTABLE |
| Scan on Push | Enabled |
| Created | FILL AFTER CREATION |

---

## Step 15 — EC2 Instance ⬜

| Resource | Value |
|----------|-------|
| Instance ID | `FILL AFTER CREATION` |
| Instance ARN | `FILL AFTER CREATION` |
| AMI | Ubuntu 22.04 LTS |
| Instance Type | `t3.small` |
| IAM Profile | `coursewright-ec2-profile` |
| Security Group | `coursewright-ec2-sg` |
| Elastic IP | `FILL AFTER CREATION` |
| Key Pair Name | `FILL AFTER CREATION` |
| Created | FILL AFTER CREATION |

---

## Step 16 — Nginx + SSL ⬜

| Resource | Value |
|----------|-------|
| Domain | `FILL WITH YOUR DOMAIN` |
| SSL Certificate | Let's Encrypt via Certbot |
| Nginx Config | `/etc/nginx/sites-available/coursewright` |
| Status | ⬜ Pending |

---

## Step 17 — Security Monitoring ⬜

### GuardDuty

| Resource | Value |
|----------|-------|
| Detector ID | `FILL AFTER CREATION` |
| Region | us-east-1 |
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
| Topic ARN | `FILL AFTER CREATION` |
| Subscription | Email → your email |
| Status | ⬜ Pending |

---

## GitHub Secrets to Add (after all AWS resources are created)

These go in GitHub → repo → Settings → Secrets and variables → Actions:

| Secret Name | Value | Available After |
|-------------|-------|-----------------|
| `AWS_ROLE_ARN` | `arn:aws:iam::YOUR_ACCOUNT_ID:role/coursewright-github-actions-role` | ✅ Now |
| `S3_BUCKET_NAME` | `coursewright-frontend-prod` | Step 12 |
| `CF_DISTRIBUTION_ID` | CloudFront distribution ID | Step 13 |
| `ECR_REPOSITORY_URI` | `YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/coursewright-backend` | Step 14 |
| `EC2_HOST` | Elastic IP address | Step 15 |
| `EC2_SSH_KEY` | Full private key content | Step 15 |
| `VITE_API_URL` | `https://yourdomain.com/api/v1` | Step 16 |

---

## Quick Reference — All ARNs

| Resource | ARN |
|----------|-----|
| EC2 Role | `arn:aws:iam::YOUR_ACCOUNT_ID:role/coursewright-ec2-role` |
| EC2 Policy | `arn:aws:iam::YOUR_ACCOUNT_ID:policy/coursewright-ec2-policy` |
| EC2 Instance Profile | `arn:aws:iam::YOUR_ACCOUNT_ID:instance-profile/coursewright-ec2-profile` |
| GitHub Actions Role | `arn:aws:iam::YOUR_ACCOUNT_ID:role/coursewright-github-actions-role` |
| GitHub Actions Policy | `arn:aws:iam::YOUR_ACCOUNT_ID:policy/coursewright-github-actions-policy` |
| RDS Endpoint | FILL AFTER STEP 10 |
| Secrets Manager | FILL AFTER STEP 11 |
| S3 Bucket | FILL AFTER STEP 12 |
| CloudFront | FILL AFTER STEP 13 |
| ECR Repository | FILL AFTER STEP 14 |
| EC2 Instance | FILL AFTER STEP 15 |
| GuardDuty Detector | FILL AFTER STEP 17 |
| CloudTrail Trail | FILL AFTER STEP 17 |
| SNS Topic | FILL AFTER STEP 17 |