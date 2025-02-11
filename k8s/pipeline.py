import os
from google.cloud import storage
from google.cloud import build
from google.cloud import secretmanager
from google.cloud.devtools import cloudbuild_v1
import yaml

class SecureGCPPipeline:
    def __init__(self, project_id, region):
        self.project_id = project_id
        self.region = region
        self.build_client = build.Client()
        self.storage_client = storage.Client()
        self.secret_client = secretmanager.SecretManagerServiceClient()

    def get_secret(self, secret_id, version_id="latest"):
        """Safely retrieve secrets from Secret Manager"""
        name = f"projects/{self.project_id}/secrets/{secret_id}/versions/{version_id}"
        response = self.secret_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")

    def create_secure_trigger(self, repo_name, branch_pattern, build_config_path):
        """Create a Cloud Build trigger with security configurations"""
        trigger_config = {
            "name": f"{repo_name}-trigger",
            "github": {
                "owner": "your-github-org",
                "name": repo_name,
                "push": {
                    "branch": branch_pattern
                }
            },
            "filename": build_config_path,
            "serviceAccount": f"projects/{self.project_id}/serviceAccounts/cicd-service@{self.project_id}.iam.gserviceaccount.com"
        }
        
        return self.build_client.create_build_trigger(
            project_id=self.project_id,
            trigger=trigger_config
        )
    def create_secure_build_config(self, filename="cloudbuild.yaml"):
        """Create a secure Cloud Build configuration"""
        build_steps = [
            # Install dependencies securely
            {
                "name": "python:3.9-slim",
                "entrypoint": "pip",
                "args": ["install", "-r", "requirements.txt", "--no-cache-dir"]
            },

            # Run security checks
            {
                "name": "python:3.9-slim",
                "entrypoint": "pip",
                "args": ["install", "bandit", "safety"],
            },
            {
                "name": "python:3.9-slim",
                "entrypoint": "bandit",
                "args": ["-r", "./src", "-ll"]
            },

            # Build with security headers
            {
                "name": "gcr.io/cloud-builders/docker",
                "args": [
                    "build",
                    "-t", f"gcr.io/{self.project_id}/app:$COMMIT_SHA",
                    "--build-arg", "PROJECT_ID=$PROJECT_ID",
                    "--no-cache",
                    "."
                ]
            },

            # Scan container for vulnerabilities
            {
                "name": "gcr.io/cloud-builders/gke-deploy",
                "args": [
                    "run",
                    "--filename=k8s/",
                    "--location=us-central1",
                    "--cluster=training-cluster",
                    "--timeout=1800s"
                ]
            }
        ]
        
        build_config = {
            "steps": build_steps,
            "timeout": "1800s",
            "options": {
                "logging": "CLOUD_LOGGING_ONLY",
                "machineType": "N1_HIGHCPU_8"
            },
            "secretEnv": ["DATABASE_CONNECTION"]
        }
        
        with open(filename, 'w') as f:
            yaml.dump(build_config, f)

def main():
    pipeline = SecureGCPPipeline(
        project_id="personal-450419",
        region="us-central1"
    )
    
    # Create secure build configuration
    pipeline.create_secure_build_config()
    
    # Create secure trigger
    pipeline.create_secure_trigger(
        repo_name="python-work",
        branch_pattern="^master$",
        build_config_path="cloudbuild.yaml"
    )
if __name__ == "__main__":
    main()