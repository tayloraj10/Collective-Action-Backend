# Collective Action Backend - Deployment

## Automated Deployment with GitHub Actions

Every push to `main` automatically deploys to Cloud Run.

### What Happens
1. Tests run on PR/non-main branches (CI)
2. On merge to `main`: Docker build → GCR push → Cloud Run deploy
3. Health check runs after deployment
4. Service URL available in GitHub Actions log

### View Deployment Status
- Go to **Actions** tab in GitHub repo
- Click workflow to see logs and deployment output
- Service URL: Check the "Deploy to Cloud Run" step output

### Environment Variables
Managed via GCP Secret Manager:
- `DATABASE_URL` - Set via `gcloud secrets create database-url`

To add more secrets:
```bash
echo "secret-value" | gcloud secrets create my-secret --data-file=-
```

Then add to `.github/workflows/deploy.yml`:
```yaml
--set-secrets "MY_VAR=my-secret:latest"
```

## Troubleshooting

**Workflow fails with "permission denied"**
- Verify GCP service account has correct roles
- Check `GCP_SA_KEY` secret is valid JSON

**Deployment succeeds but service unavailable**
- Check Cloud SQL connection: `gcloud sql connect collective-action-db --user=postgres`
- Verify `DATABASE_URL` secret is set: `gcloud secrets describe database-url`

**View Cloud Run logs**
```bash
gcloud run services logs tail collective-action-backend --region=us-central1
```

## Manual Steps (if needed)

### Build & Deploy Locally
```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/collective-action-backend
gcloud run deploy collective-action-backend \
  --image gcr.io/PROJECT_ID/collective-action-backend \
  --region us-central1
```
Required IAM roles for the service account:
- roles/run.admin
- roles/storage.admin
- roles/cloudsql.client
- roles/secretmanager.secretAccessor
- roles/iam.serviceAccountUser
### Delete Resources
```bash
gcloud run services delete collective-action-backend --region=us-central1
gcloud sql instances delete collective-action-db
gcloud secrets delete database-url
```

### One-Time Setup

#### 1. Create Google Cloud Service Account

```bash
# Set your project ID
export PROJECT_ID="your-project-id"

# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

#### 2. Set Up Cloud SQL Database

```bash
# Enable APIs
gcloud services enable sqladmin.googleapis.com run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com

# Create Cloud SQL instance (takes ~5 minutes)
gcloud sql instances create collective-action-db \
  --database-version=POSTGRES_17 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --root-password=YOUR_SECURE_PASSWORD

# Create database
gcloud sql databases create app_db --instance=collective-action-db

# Create database URL secret
echo "postgresql+psycopg2://postgres:YOUR_PASSWORD@/app_db?host=/cloudsql/${PROJECT_ID}:us-central1:collective-action-db" | \
  gcloud secrets create database-url --data-file=-
```

#### 3. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

- **`GCP_PROJECT_ID`**: Your GCP project ID (e.g., `my-project-123`)
- **`GCP_SA_KEY`**: Contents of `github-actions-key.json` (entire JSON file)

#### 4. Push to Main Branch

```bash
git add .
git commit -m "Set up CI/CD"
git push origin main
```

🎉 **Done!** GitHub Actions will automatically deploy on every push to `main`.

### Workflow Features

- **CI on Pull Requests**: Lints, tests, and builds Docker image
- **Auto-Deploy on Main**: Deploys to Cloud Run when merged
- **Health Checks**: Verifies deployment success
- **Manual Trigger**: Deploy anytime via GitHub Actions UI

### View Deployment Status

- Go to **Actions** tab in your GitHub repo
- Click on latest workflow run
- See deployment logs and service URL

---

## Manual Deployment (Alternative)

### Prerequisites

1. **Google Cloud CLI installed**
   ```powershell
   choco install gcloudsdk
   ```

2. **Authenticate with Google Cloud**
   ```powershell
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Create a GCP project** (or use existing)
   - Go to https://console.cloud.google.com
   - Create new project or note your project ID

## Quick Deploy

Run the deployment script:

```powershell
.\deploy.ps1 -ProjectId "your-project-id"
```

Optional parameters:
- `-Region`: GCP region (default: `us-central1`)
- `-ServiceName`: Cloud Run service name (default: `collective-action-backend`)
- `-DbInstance`: Cloud SQL instance name (default: `collective-action-db`)
- `-DbName`: Database name (default: `app_db`)

Example with custom region:
```powershell
.\deploy.ps1 -ProjectId "my-project" -Region "us-east1"
```

## What the script does

1. ✅ Enables required GCP APIs
2. ✅ Creates Cloud SQL PostgreSQL instance (if needed)
3. ✅ Sets up database credentials in Secret Manager
4. ✅ Builds Docker container with Cloud Build
5. ✅ Deploys to Cloud Run with Cloud SQL connection
6. ✅ Returns your service URL

## Manual Steps

### 1. Set Database Password (First Time Only)

```powershell
gcloud sql users set-password postgres `
  --instance=collective-action-db `
  --password=YOUR_SECURE_PASSWORD
```

### 2. Update Code & Redeploy

```powershell
# Build new image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/collective-action-backend

# Deploy update
gcloud run deploy collective-action-backend `
  --image gcr.io/YOUR_PROJECT_ID/collective-action-backend `
  --region us-central1
```

### 3. View Logs

```powershell
gcloud run services logs tail collective-action-backend --region=us-central1
```

### 4. Connect to Cloud SQL (Optional)

```powershell
gcloud sql connect collective-action-db --user=postgres
```

## Environment Variables

Managed via Secret Manager:
- `DATABASE_URL` - PostgreSQL connection string (auto-configured)

To add more secrets:
```powershell
echo "secret-value" | gcloud secrets create my-secret --data-file=-

gcloud run services update collective-action-backend `
  --set-secrets "MY_VAR=my-secret:latest" `
  --region us-central1
```

## Cost Estimates (Free Tier Eligible)

- **Cloud Run**: First 2M requests/month free
- **Cloud SQL**: ~$7/month for db-f1-micro
- **Cloud Build**: 120 build-minutes/day free
- **Secret Manager**: 6 active secrets free

## Cleanup (Delete All Resources)

```powershell
# Delete Cloud Run service
gcloud run services delete collective-action-backend --region=us-central1

# Delete Cloud SQL instance
gcloud sql instances delete collective-action-db

# Delete secrets
gcloud secrets delete database-url

# Delete container images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/collective-action-backend
```

## Troubleshooting

**Issue**: Service returns 503
- Check logs: `gcloud run services logs tail collective-action-backend`
- Verify database connection in Secret Manager

**Issue**: Build fails
- Check Dockerfile syntax
- Verify requirements.txt has all dependencies

**Issue**: Database connection fails
- Verify Cloud SQL instance is running
- Check DATABASE_URL secret format
- Ensure Cloud SQL connection is added to service

## Next Steps

- [ ] Set up custom domain
- [ ] Add CI/CD with GitHub Actions
- [ ] Enable Cloud Armor for DDoS protection
- [ ] Set up monitoring with Cloud Logging
- [ ] Configure auto-scaling limits
