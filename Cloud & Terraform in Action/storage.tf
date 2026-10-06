# 4 random bytes -> 8 hex chars. S3 bucket names are global and IAM names are
# account-wide, so a suffix avoids collisions with anything that already exists.
resource "random_id" "suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "site" {
  bucket        = "${var.project_name}-site-${random_id.suffix.hex}"
  force_destroy = true # lets `terraform destroy` remove it even with objects inside

  tags = {
    Name = "${var.project_name}-site-${random_id.suffix.hex}"
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket = aws_s3_bucket.site.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "site" {
  bucket = aws_s3_bucket.site.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# The web page lives in the (private) bucket. EC2 downloads it at boot using
# its instance role, so the bucket never has to be public.
resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.site.id
  key          = "site/index.html"
  content_type = "text/html"
  content = templatefile("${path.module}/templates/index.html.tftpl", {
    project_name = var.project_name
    region       = var.aws_region
    bucket_name  = aws_s3_bucket.site.bucket
    vpc_cidr     = var.vpc_cidr
    subnet_cidr  = var.public_subnet_cidr
  })
}
