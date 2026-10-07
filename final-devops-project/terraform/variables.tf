variable "aws_region" {
  description = "AWS region for every resource"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Environment name, used in tags and resource names"
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Owner tag, so stray resources can be traced back to a person"
  type        = string
  default     = "saptak-banerjee"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
  default     = "clinicdesk-eks"
}

variable "kubernetes_version" {
  description = "EKS control-plane Kubernetes version"
  type        = string
  default     = "1.36"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.42.0.0/16"
}

variable "node_instance_types" {
  description = "Instance types for the managed node group"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum worker nodes"
  type        = number
  default     = 1
}

variable "node_desired_size" {
  description = "Desired worker nodes"
  type        = number
  default     = 2
}

variable "node_max_size" {
  description = "Maximum worker nodes"
  type        = number
  default     = 3
}

variable "endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public EKS API endpoint (narrow this to your own IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
