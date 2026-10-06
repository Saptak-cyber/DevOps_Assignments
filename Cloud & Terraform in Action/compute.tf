# ---------- IAM: what the instance is allowed to do ----------

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "web" {
  name               = "${var.project_name}-web-role-${random_id.suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
}

# Least privilege: read objects under site/ in this one bucket, nothing else.
resource "aws_iam_role_policy" "read_site" {
  name = "read-site-object"
  role = aws_iam_role.web.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject"]
      Resource = "${aws_s3_bucket.site.arn}/site/*"
    }]
  })
}

# Lets SSM Session Manager / Run Command reach the instance, which is how we
# get a shell without opening port 22.
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.web.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_instance_profile" "web" {
  name = "${var.project_name}-web-profile-${random_id.suffix.hex}"
  role = aws_iam_role.web.name
}

# ---------- EC2 ----------

resource "aws_instance" "web" {
  ami                    = data.aws_ami.al2023.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.web.id]
  iam_instance_profile   = aws_iam_instance_profile.web.name

  user_data = templatefile("${path.module}/templates/user_data.sh.tftpl", {
    bucket_name  = aws_s3_bucket.site.bucket
    object_key   = aws_s3_object.index.key
    region       = var.aws_region
    project_name = var.project_name
  })
  user_data_replace_on_change = true

  # IMDSv2 only (session tokens), blocks SSRF-style metadata theft.
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  root_block_device {
    volume_type = "gp3"
    volume_size = 8
    encrypted   = true
  }

  volume_tags = merge(var.common_tags, {
    Name = "${var.project_name}-web-root"
  })

  tags = {
    Name = "${var.project_name}-web"
  }

  # Explicit dependencies. Nothing in this resource *references* these, so
  # without depends_on Terraform could launch the instance in parallel with them:
  #  - the route table association: user_data runs `dnf install nginx` on first
  #    boot and needs the 0.0.0.0/0 -> IGW route to already exist;
  #  - the inline S3 read policy and the SSM attachment: the instance profile
  #    only references the role, so the role's permissions could still be
  #    missing when user_data runs `aws s3 cp`.
  depends_on = [
    aws_route_table_association.public,
    aws_iam_role_policy.read_site,
    aws_iam_role_policy_attachment.ssm_core,
  ]
}
