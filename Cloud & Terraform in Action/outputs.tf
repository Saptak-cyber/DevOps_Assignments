output "vpc_id" {
  description = "ID of the project VPC."
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC."
  value       = aws_vpc.main.cidr_block
}

output "public_subnet_id" {
  description = "ID of the public subnet."
  value       = aws_subnet.public.id
}

output "security_group_id" {
  description = "ID of the web security group."
  value       = aws_security_group.web.id
}

output "ami_id" {
  description = "Amazon Linux 2023 AMI used for the instance."
  value       = data.aws_ami.al2023.id
}

output "ami_name" {
  description = "Name of that AMI."
  value       = data.aws_ami.al2023.name
}

output "instance_id" {
  description = "ID of the EC2 instance."
  value       = aws_instance.web.id
}

output "instance_public_ip" {
  description = "Public IPv4 address of the EC2 instance."
  value       = aws_instance.web.public_ip
}

output "website_url" {
  description = "URL of the nginx site."
  value       = "http://${aws_instance.web.public_ip}/"
}

output "site_bucket" {
  description = "Private S3 bucket holding the site content."
  value       = aws_s3_bucket.site.bucket
}

output "site_object_uri" {
  description = "S3 URI of the page the instance downloads at boot."
  value       = "s3://${aws_s3_bucket.site.bucket}/${aws_s3_object.index.key}"
}
