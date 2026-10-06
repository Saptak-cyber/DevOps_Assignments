# Screenshot capture checklist — Terraform & Infrastructure as Code

The READMEs reference these filenames. Capture each one from your terminal and save it here
with the exact name, and the images in the READMEs will render on GitHub.

All AWS resources were destroyed after the run. To capture 01–08, re-run the workflow in
`terraform-s3-demo/` (`init` → `fmt` → `validate` → `plan` → `apply` → `show` → `output` →
`aws s3api …` → `destroy`) and screenshot each step. A new random suffix will appear in the bucket name.

| File | What to capture | Referenced from |
| --- | --- | --- |
| `01-tf-init.png` | `terraform init` installing aws + random providers | terraform-s3-demo/README.md |
| `02-tf-fmt-validate.png` | `terraform fmt -check`, `terraform fmt`, `terraform validate` → Success | terraform-s3-demo/README.md |
| `03-tf-plan.png` | `terraform plan` → `Plan: 6 to add` | terraform-s3-demo/README.md |
| `04-tf-apply.png` | `terraform apply -auto-approve` → `Apply complete! Resources: 6 added` + outputs | README.md, terraform-s3-demo/README.md |
| `05-tf-show.png` | `terraform show` (bucket resource with `tags_all`) | terraform-s3-demo/README.md |
| `06-tf-output.png` | `terraform output` and `terraform state list` | terraform-s3-demo/README.md |
| `07-s3-verify-cli.png` | `aws s3api get-bucket-versioning / get-bucket-encryption / get-public-access-block` and `list-object-versions` | terraform-s3-demo/README.md, aws-services/03-s3/README.md |
| `08-tf-destroy.png` | `terraform destroy` → `Destroy complete! Resources: 6 destroyed.` + `head-bucket` 404 | terraform-s3-demo/README.md |
| `09-iam-cli.png` | `aws iam get-user`, `list-attached-user-policies`, `simulate-custom-policy` | aws-services/01-iam/README.md |
| `10-ec2-cli.png` | `aws ec2 describe-instance-types --instance-types t2.micro t3.micro` and the AL2023 `describe-images` table | aws-services/02-ec2/README.md |
| `11-vpc-cli.png` | default VPC `describe-subnets` and `describe-network-acls` tables | aws-services/04-vpc/README.md |
| `12-dynamodb-cli.png` | DynamoDB `create-table` → `put-item` → `query` with `begins_with` | README.md, aws-services/05-dynamodb-rds/README.md |
| `13-rds-cli.png` | `aws rds describe-db-engine-versions --engine postgres --default-only` and `describe-orderable-db-instance-options` | aws-services/05-dynamodb-rds/README.md |

Every command needed is in the README that references the screenshot.
