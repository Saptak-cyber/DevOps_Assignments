# AWS publishes the current Amazon Linux 2023 AMI ID for each region as a
# public SSM parameter. Reading it means we never hard-code an AMI ID that
# goes stale (or differs between regions).
data "aws_ssm_parameter" "al2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# Look the AMI up so its name / creation date can be shown and checked.
data "aws_ami" "al2023" {
  owners = ["amazon"]

  filter {
    name   = "image-id"
    values = [data.aws_ssm_parameter.al2023.insecure_value]
  }
}
