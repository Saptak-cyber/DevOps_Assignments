variable "aws_region" {
  description = "AWS region where the S3 bucket will be created."
  type        = string
  default     = "ap-south-1"
}

variable "bucket_name_prefix" {
  description = "Prefix for the bucket name. A random hex suffix is appended because S3 bucket names are globally unique."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{2,40}$", var.bucket_name_prefix))
    error_message = "Use 3-41 lowercase letters, digits or hyphens (the suffix adds 9 more characters)."
  }
}

variable "noncurrent_version_retention_days" {
  description = "How many days an overwritten/deleted (noncurrent) object version is kept before S3 expires it."
  type        = number
  default     = 30
}

variable "common_tags" {
  description = "Tags applied to every resource via the provider's default_tags."
  type        = map(string)
  default     = {}
}
