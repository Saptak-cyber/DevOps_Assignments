variable "aws_region" {
  description = "AWS region for every resource in this project."
  type        = string
  default     = "ap-south-1"
}

variable "project_name" {
  description = "Prefix used in every Name tag and resource name."
  type        = string
  default     = "sst-s19-cloud-tf"
}

variable "vpc_cidr" {
  description = "CIDR block of the VPC."
  type        = string
  default     = "10.20.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "vpc_cidr must be a valid IPv4 CIDR block, e.g. 10.20.0.0/16."
  }
}

variable "public_subnet_cidr" {
  description = "CIDR block of the public subnet (must sit inside vpc_cidr)."
  type        = string
  default     = "10.20.1.0/24"
}

variable "az_suffix" {
  description = "AZ letter for the public subnet. t2.micro is offered in ap-south-1a and ap-south-1b only."
  type        = string
  default     = "a"
}

variable "instance_type" {
  description = "EC2 instance type. Restricted to free-tier-eligible sizes."
  type        = string
  default     = "t2.micro"

  validation {
    condition     = contains(["t2.micro", "t3.micro"], var.instance_type)
    error_message = "Only t2.micro or t3.micro are allowed in this project (free tier)."
  }
}

variable "common_tags" {
  description = "Tags applied to every resource through the provider's default_tags."
  type        = map(string)
  default = {
    Project   = "sst-devops-homework"
    ManagedBy = "Terraform"
    Session   = "19"
  }
}
