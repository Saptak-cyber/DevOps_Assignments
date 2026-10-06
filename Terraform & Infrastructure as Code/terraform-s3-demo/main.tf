# 4 random bytes -> 8 hex characters, e.g. "3f9a1c07".
# Stored in state, so the name stays stable across plans until destroy.
resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "demo" {
  bucket = "${var.bucket_name_prefix}-${random_id.suffix.hex}"

  # Lets `terraform destroy` delete the bucket even if it still holds
  # objects / old versions. Fine for a demo; never for real data.
  force_destroy = true

  tags = {
    Name    = "${var.bucket_name_prefix}-${random_id.suffix.hex}"
    Session = "18"
  }
}

# Keep every version of every object (protects against overwrite/delete).
resource "aws_s3_bucket_versioning" "demo" {
  bucket = aws_s3_bucket.demo.id

  versioning_configuration {
    status = "Enabled"
  }
}

# Default encryption at rest with S3-managed keys (SSE-S3 / AES256).
resource "aws_s3_bucket_server_side_encryption_configuration" "demo" {
  bucket = aws_s3_bucket.demo.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block every form of public access (ACLs and bucket policies).
resource "aws_s3_bucket_public_access_block" "demo" {
  bucket = aws_s3_bucket.demo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Versioning without a lifecycle rule grows forever; expire old versions.
resource "aws_s3_bucket_lifecycle_configuration" "demo" {
  bucket = aws_s3_bucket.demo.id

  rule {
    id     = "expire-noncurrent-versions"
    status = "Enabled"

    filter {}

    noncurrent_version_expiration {
      noncurrent_days = var.noncurrent_version_retention_days
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  # A lifecycle rule on noncurrent versions only makes sense once
  # versioning is on, and S3 can reject the two calls racing each other.
  depends_on = [aws_s3_bucket_versioning.demo]
}
