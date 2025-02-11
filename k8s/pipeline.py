import os
from google.cloud import storage
from google.cloud import build
from google.cloud.devtools import cloudbuild_v1
import yaml

class GCPPipeline:
    def __init__(self, project_id, region):
        """
        Initialize the CI/CD pipeline with GCP project details
        
        Args:
            project_id (str): Google Cloud Project ID
            region (str): GCP region (e.g., 'us-central1')
        """
        self.project_id = project_id
        self.region = region
        self.build_client = build.Client()
        self.storage_client = storage.Client()

    def create_trigger(self, repo_name, branch_pattern, build_config_path):
        """
        Create a Cloud Build trigger for the repository
        
        Args:
            repo_name (str): Name of the repository
            branch_pattern (str): Branch pattern to trigger builds (e.g., '^main$')
            build_config_path (str): Path to cloudbuild.yaml in the repo
        """
        trigger_config = {
            "name": f"{repo_name}-trigger",
            "github": {
                "owner": "your-github-org",
                "name": repo_name,
                "push": {
                    "branch": branch_pattern
                }
            },
            "filename": build_config_path
        }
        
        operation = self.build_client.create_build_trigger(
            project_id=self.project_id,
            trigger=trigger_config
        )
        return operation

    def create_build_config(self, steps, filename="cloudbuild.yaml"):
        """
        Create a Cloud Build configuration file
        
        Args:
            steps (list): List of build steps
            filename (str): Output filename for the config
        """
        build_config = {
            "steps": steps,
            "timeout": "1800s"
        }
        
        with open(filename, 'w') as f:
            yaml.dump(build_config, f)

    def run_pipeline(self, source_path, build_config):
        """
        Manually trigger a pipeline run
        
        Args:
            source_path (str): Path to source code
            build_config (dict): Build configuration
        """
        build = self.build_client.create_build(
            project_id=self.project_id,
            build={
                "source": {"storage_source": source_path},
                "steps": build_config["steps"]
            }
        )
        return build

    def setup_deployment_environment(self, env_name, env_vars):
        """
        Setup deployment environment variables
        
        Args:
            env_name (str): Environment name (e.g., 'prod', 'dev')
            env_vars (dict): Environment variables
        """
        from google.cloud import secretmanager
        
        secret_client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{self.project_id}"

        for key, value in env_vars.items():
            secret_id = f"{env_name}_{key}"
            
            secret = secret_client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_id,
                    "secret": {"replication": {"automatic": {}}}
                }
            )
            
            secret_client.add_secret_version(
                request={
                    "parent": secret.name,
                    "payload": {"data": value.encode("UTF-8")}
                }
            )

def main():
    # Example usage
    pipeline = GCPPipeline(
        project_id="personal-450419",
        region="us-central1"
    )
    
    # Define build steps with dependency installation
    build_steps = [
        # Install Python dependencies
        {
            "name": "python:3.9",
            "entrypoint": "pip",
            "args": ["install", "-r", "requirements.txt", "-t", "/workspace/lib"]
        },
        # Run tests
        {
            "name": "python:3.9",
            "entrypoint": "python",
            "args": ["-m", "pytest", "tests/"],
            "env": ["PYTHONPATH=/workspace/lib"]
        },
        # Build Docker image
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["build", "-t", "gcr.io/$personal-450419/app:$COMMIT_SHA", "."]
        },
        # Push Docker image
        {
            "name": "gcr.io/cloud-builders/docker",
            "args": ["push", "gcr.io/$personal-450419/app:$COMMIT_SHA"]
        },
        # Deploy to GKE
        {
            "name": "gcr.io/cloud-builders/gke-deploy",
            "args": [
                "run",
                "--filename=k8s/",
                "--location=us-central1",
                "--cluster=autopilot-cluster1"
            ]
        }
    ]
    
    # Create build configuration
    pipeline.create_build_config(build_steps)
    
    # Create trigger
    pipeline.create_trigger(
        repo_name="Phython-work",
        branch_pattern="^main$",
        build_config_path="cloudbuild.yaml"
    )
    
    # Setup environment variables
    env_vars = {
        "DATABASE_URL": "personal-450419:us-central1:training-2-2025",
        "API_KEY": "4d1bf14cd3113596af0159576b5026ddbb2fd252"
    }
    pipeline.setup_deployment_environment("prod", env_vars)

if __name__ == "__main__":
    main()