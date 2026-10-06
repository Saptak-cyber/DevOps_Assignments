# No secrets here: credentials come from the AWS credential chain, never from tfvars.
aws_region         = "ap-south-1"
bucket_name_prefix = "saptak-tf-s3-demo"

noncurrent_version_retention_days = 30

common_tags = {
  Project     = "sst-devops-homework"
  ManagedBy   = "Terraform"
  Environment = "dev"
  Owner       = "saptak-banerjee"
}
