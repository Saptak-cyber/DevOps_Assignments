terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # Talks to the AWS APIs (VPC, EC2, S3, IAM).
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    # Pure-Terraform provider: generates a random suffix kept in state.
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# No credentials here: the AWS provider reads them from the standard
# credential chain (env vars, ~/.aws/credentials, SSO, instance role).
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = var.common_tags
  }
}
