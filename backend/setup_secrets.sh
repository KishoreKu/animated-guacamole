#!/bin/bash
PROJECT="ghibli-prod-2026"
SA="github-actions-deployer@ghibli-prod-2026.iam.gserviceaccount.com"
PROJECT_NUM="226609348101"
COMPUTE_SA="${PROJECT_NUM}-compute@developer.gserviceaccount.com"

echo "Enabling API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT
sleep 5

for secret in OPENROUTER_API_KEY FAL_KEY SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY CRON_SECRET_TOKEN; do
    echo "Creating $secret..."
    gcloud secrets create $secret --replication-policy="automatic" --project=$PROJECT || true
    gcloud secrets add-iam-policy-binding $secret --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor" --project=$PROJECT >/dev/null
    gcloud secrets add-iam-policy-binding $secret --member="serviceAccount:$COMPUTE_SA" --role="roles/secretmanager.secretAccessor" --project=$PROJECT >/dev/null
done

cd /Users/kishorekumar/CascadeProjects/ghibili/backend

echo "Adding values..."
grep '^OPENROUTER_API_KEY=' .env | cut -d '=' -f 2- | gcloud secrets versions add OPENROUTER_API_KEY --data-file=- --project=$PROJECT
grep '^FAL_KEY=' .env | cut -d '=' -f 2- | gcloud secrets versions add FAL_KEY --data-file=- --project=$PROJECT
grep '^SUPABASE_URL=' .env | cut -d '=' -f 2- | gcloud secrets versions add SUPABASE_URL --data-file=- --project=$PROJECT
grep '^SUPABASE_SERVICE_ROLE_KEY=' .env | cut -d '=' -f 2- | gcloud secrets versions add SUPABASE_SERVICE_ROLE_KEY --data-file=- --project=$PROJECT

echo "random_cron_token_$(date +%s)" | gcloud secrets versions add CRON_SECRET_TOKEN --data-file=- --project=$PROJECT

echo "Done!"
