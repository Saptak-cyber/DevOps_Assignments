# Screenshots — Cloud & Terraform in Action

The README references these filenames, and every one of them is in this folder.

| File | What it shows |
| --- | --- |
| `01-vpc-resource-map.png` | AWS console → VPC → `sst-s19-cloud-tf-vpc` → **Resource map** tab (subnet, route table, IGW) |
| `02-tf-init-validate.png` | `terraform init`, `terraform fmt -recursive`, `terraform validate` → Success |
| `03-tf-plan.png` | `terraform plan -out=tfplan` → `Plan: 16 to add` + `Saved the plan to: tfplan` |
| `04-tf-apply.png` | `terraform apply tfplan` → `aws_instance.web: Creating...` last, `Apply complete! Resources: 16 added` + outputs |
| `05-nginx-page.png` | Browser at `http://<instance_public_ip>/` showing the page with the instance ID and AZ |
| `06-aws-cli-resources.png` | `aws ec2 describe-instances / describe-vpcs / describe-route-tables` tables filtered by `tag:Project` |
| `07-ssm-run-command.png` | `aws ssm get-command-invocation` output (`active`, nginx listening on :80, cloud-init finished) |
| `08-tf-state.png` | `terraform state list` and the top of `terraform state show aws_instance.web` |
| `09-tf-destroy.png` | `terraform destroy` → `Destroy complete! Resources: 16 destroyed.` + empty `describe-vpcs` / 404 `head-bucket` |

Every command needed is in the README, in the section that references the screenshot.

## How these screenshots were produced

Terminal screenshots are renderings of the real command output already captured in the README (same commands, same output; very long outputs are trimmed with a marked `[… lines trimmed …]` line).

`01-vpc-resource-map.png` and `05-nginx-page.png` are live captures (AWS console and browser) from a re-apply of this same project on 2026-10-07, so the VPC, instance and bucket IDs differ from the README output; the stack was destroyed again right after. The account ID is masked as `<account-id>`.
