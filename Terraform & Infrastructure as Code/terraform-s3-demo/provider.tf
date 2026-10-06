terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Credentials are NOT configured here. The provider picks them up from the
# standard AWS credential chain (env vars / ~/.aws/credentials / SSO).
provider "aws" {
  region = var.aws_region

  # Applied to every taggable resource this provider creates.
  default_tags {
    tags = var.common_tags
  }
}
