# Terraform & Infrastructure as Code

**Author:** Saptak Banerjee
**Course:** SST DevOps & Cloud [SWE]
**Session:** 18 — Terraform & Infrastructure as Code
**Source material:** [`devops-heros/session18-terraform-iac`](https://github.com/Nency-Ravaliya/devops-heros/tree/main/session18-terraform-iac)

**Environment:** Terraform **v1.16.4**, AWS provider **v6.67.0**, AWS CLI **v2.35.19**, against a real AWS account in **ap-south-1** (Mumbai) as the IAM user `terraform-sandbox`. Every output is a real capture, with the account ID masked as `<account-id>`. Everything created was destroyed the same day (see [Cleanup](#cleanup)).

---

## Table of Contents

| # | Task | Where |
| --- | --- | --- |
| 1 | [Terraform S3 Demo](#task-1-terraform-s3-demo) | [`terraform-s3-demo/README.md`](./terraform-s3-demo/README.md) |
| 2 | [AWS Services Research](#task-2-aws-services-research) | [`aws-services/`](./aws-services/) |
| — | [Cleanup](#cleanup) | |

```text
Terraform & Infrastructure as Code/
├── README.md                     ← this file
├── terraform-s3-demo/            ← Task 1
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── provider.tf
│   ├── terraform.tfvars          (no secrets)
│   ├── README.md                 (complete workflow with real output)
│   ├── .gitignore
│   └── .terraform.lock.hcl
├── aws-services/                 ← Task 2
│   ├── 01-iam/README.md
│   ├── 02-ec2/README.md
│   ├── 03-s3/README.md
│   ├── 04-vpc/README.md
│   └── 05-dynamodb-rds/README.md
└── screenshots/
```

---

## What Infrastructure as Code means here

Instead of clicking through the console, the S3 bucket and its settings are **declared** in `.tf` files. Terraform:

1. reads the desired state (`*.tf` + `terraform.tfvars`);
2. compares it with the recorded state (`terraform.tfstate`) and with what AWS actually has (refresh);
3. builds a **dependency graph** and calls the AWS APIs needed to close the gap, in parallel where it can.

The same files can be reviewed in a PR, re-applied in another account, and destroyed cleanly. All three properties showed up in the run: `plan` printed the exact diff, a second `plan` reported `No changes`, and `destroy` removed all 6 resources, including a non-empty versioned bucket.

---

## Task 1: Terraform S3 Demo

**Full write-up with every command and its real output:** [`terraform-s3-demo/README.md`](./terraform-s3-demo/README.md)

The project uses exactly the requested layout (`main.tf`, `variables.tf`, `outputs.tf`, `provider.tf`, `terraform.tfvars`, `README.md`) and creates a private, encrypted, versioned S3 bucket with a lifecycle rule. Two providers are used: `hashicorp/aws` and `hashicorp/random`, the latter for a globally unique name suffix.

| Step | Command | Result |
| --- | --- | --- |
| 1 | `terraform init` | aws v6.67.0 + random v3.9.1 installed, lock file written |
| 2 | `terraform fmt` | no changes needed (`fmt -check` clean) |
| 3 | `terraform validate` | `Success! The configuration is valid.` |
| 4 | `terraform plan` | `Plan: 6 to add, 0 to change, 0 to destroy.` |
| 5 | `terraform apply -auto-approve` | `Apply complete! Resources: 6 added` → bucket `saptak-tf-s3-demo-b53eac94` |
| 6 | `terraform show` | full state incl. `tags_all` with `Project=sst-devops-homework`, `ManagedBy=Terraform` |
| 7 | `terraform output` | 5 outputs (name, ARN, region, regional endpoint, versioning status) |
| — | `aws s3api …` | versioning `Enabled`, SSE `AES256`, all 4 public-access blocks `true`, lifecycle rule present. Overwriting an object produced 2 versions. |
| — | `terraform plan -detailed-exitcode` | `No changes.`, exit 0 (no drift) |
| 8 | `terraform destroy -auto-approve` | `Destroy complete! Resources: 6 destroyed.` → `head-bucket` returns 404 |

What the run showed:

- **Implicit dependencies** (`bucket = aws_s3_bucket.demo.id`) let Terraform create versioning, encryption and the public-access block **in parallel** once the bucket existed.
- One **explicit `depends_on`** (lifecycle → versioning) serialised the one pair that had no reference between them. `destroy` then ran the same graph in reverse.
- `force_destroy = true` let `destroy` delete a bucket that still contained 2 object versions.
- The aws provider's `default_tags` put the required tags on every resource without repeating them per resource.

**Screenshot:** ![terraform apply](./screenshots/04-tf-apply.png)

---

## Task 2: AWS Services Research

One README per service, each covering exactly the topics listed in the assignment. Where it was free or near-free, the notes include real, mostly read-only AWS CLI output from the same account, so the descriptions can be checked against an actual account rather than only the docs.

| # | Service | README | Topics | Real evidence included |
| --- | --- | --- | --- | --- |
| 01 | **IAM — Governance** | [`aws-services/01-iam/README.md`](./aws-services/01-iam/README.md) | What is IAM, Users, Groups, Roles, Policies, Permissions, Least privilege, Best practices, Use cases | `get-user`, attached `AdministratorAccess` document, account summary (root MFA on, no root keys), `simulate-custom-policy` showing allow vs implicit deny |
| 02 | **EC2 — Compute** | [`aws-services/02-ec2/README.md`](./aws-services/02-ec2/README.md) | What is EC2, AMI, Instance types, Key pairs, Security Groups, EBS, Public vs private IP, Instance lifecycle, Use cases | latest AL2023 AMI via SSM, `t2.micro` vs `t3.micro` specs and free-tier flag, AZ offerings, EBS default encryption off |
| 03 | **S3 — Storage** | [`aws-services/03-s3/README.md`](./aws-services/03-s3/README.md) | What is S3, Buckets, Objects, Storage classes, Versioning, Lifecycle policies, Encryption, Bucket policies, Use cases | Task 1 bucket: versions, lifecycle, SSE. Session 19 private bucket returning 403 to anonymous requests. |
| 04 | **VPC — Networking** | [`aws-services/04-vpc/README.md`](./aws-services/04-vpc/README.md) | What is VPC, CIDR, Subnets, Route tables, IGW, NAT Gateway, Security Groups, NACLs, Public vs private subnet | default VPC: `/20` subnets with 4,091 free IPs (5 reserved), route table → IGW, default NACL rules 100/32767, self-referencing default SG |
| 05 | **DynamoDB & RDS — Databases** | [`aws-services/05-dynamodb-rds/README.md`](./aws-services/05-dynamodb-rds/README.md) | DynamoDB: NoSQL, Tables, Items, Attributes, Partition key, Sort key, Use cases. RDS: Relational, Engines, DB instances, Security, Backups, Multi-AZ, Read replicas, Use cases | on-demand table: create → put 3 items → `begins_with` sort-key query → query without partition key rejected → delete. RDS engine list, PostgreSQL 18.3 default, `db.t4g.micro` capabilities. |

Not run, on purpose: **no RDS instance and no NAT gateway** were created. Both bill per hour, and the read-only APIs answer the research questions.

**Screenshot:** ![DynamoDB demo](./screenshots/12-dynamodb-cli.png)

---

## Cleanup

Task 1 was torn down with `terraform destroy` (output in the [sub-README](./terraform-s3-demo/README.md#9-terraform-destroy)). The DynamoDB table was deleted with `delete-table` + `wait table-not-exists`. Final check that nothing tagged for this homework remains in ap-south-1:

```bash
cd terraform-s3-demo && terraform destroy -auto-approve
aws dynamodb delete-table --table-name sst-s18-bookings
aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=sst-devops-homework
rm -rf .terraform terraform.tfstate terraform.tfstate.backup   # local working files, git-ignored
```

The result of that final tag query (run after both Session 18 and Session 19 were destroyed) is recorded in the [Session 19 cleanup section](../Cloud%20%26%20Terraform%20in%20Action/README.md#cleanup).

---

## Resources

- https://developer.hashicorp.com/terraform/tutorials/aws-get-started
- https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/s3_bucket
- https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html
- https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
- https://docs.aws.amazon.com/vpc/latest/userguide/what-is-amazon-vpc.html
- https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html
- https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html
