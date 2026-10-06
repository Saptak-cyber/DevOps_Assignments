# 03. S3 — Storage

**Author:** Saptak Banerjee · **Session:** 18 — Terraform & Infrastructure as Code (Task 2)
**Evidence:** the real bucket built in [Task 1 — `terraform-s3-demo`](../../terraform-s3-demo/README.md) (versioning, SSE, public-access block, lifecycle) and the private site bucket from [Session 19](../../../Cloud%20%26%20Terraform%20in%20Action/README.md). Both have since been destroyed.

---

## Table of Contents

1. [What is S3?](#what-is-s3)
2. [Buckets](#buckets)
3. [Objects](#objects)
4. [Storage classes](#storage-classes)
5. [Versioning](#versioning)
6. [Lifecycle policies](#lifecycle-policies)
7. [Encryption](#encryption)
8. [Bucket policies](#bucket-policies-and-access-control)
9. [Common use cases](#common-use-cases)

---

## What is S3?

**Simple Storage Service** is object storage behind an HTTPS API: you `PUT` and `GET` whole objects by key. It is not a file system (no in-place edits, no real directories) and not a block device. It is designed for **11 nines (99.999999999 %) durability**: standard classes store data redundantly across at least 3 AZs. Since December 2020 S3 has had **strong read-after-write consistency** for all operations. You pay for GB stored per month, requests, and data transferred out. There is no capacity to provision.

---

## Buckets

A **bucket** is the top-level container.

- **Globally unique name** across *all* AWS accounts, 3–63 chars, lowercase letters, digits, hyphens. That is why Task 1 appends a `random_id` (`saptak-tf-s3-demo-b53eac94`) and Terraform state records `bucket_namespace = "global"`.
- Created in **one region** (`"BucketRegion": "ap-south-1"` from `head-bucket`). Data never leaves it unless you replicate it.
- Bucket-level settings: versioning, default encryption, public-access block, lifecycle, policy, CORS, logging, replication, Object Lock, tags.
- A bucket must be **empty** before it can be deleted. Terraform's `force_destroy = true` empties it first (Task 1 destroyed a bucket that still held 2 object versions).

---

## Objects

An **object** = **key** (the full "path", e.g. `site/index.html`) + **data** (0 B to 5 TB; a single PUT handles up to 5 GB, larger needs **multipart upload**) + **metadata** (system metadata such as `Content-Type` and `ETag`, plus user `x-amz-meta-*`) + optional tags + a version ID.

"Folders" are just key prefixes and `/` has no special meaning. That is why Session 19's IAM policy can grant `arn:aws:s3:::<bucket>/site/*` and nothing else. Session 19 uploaded the page with the right `Content-Type`, which nginx later served:

```
$ aws s3 ls s3://sst-s19-cloud-tf-site-c84c1873/ --recursive
2026-10-07 04:56:19        591 site/index.html
```

---

## Storage classes

Chosen **per object**. They trade storage price against retrieval price and latency.

| Class | AZs | Min duration | Retrieval | Typical use |
| --- | --- | --- | --- | --- |
| **S3 Standard** | ≥3 | — | ms, no fee | hot data, websites, default |
| **S3 Intelligent-Tiering** | ≥3 | — | ms (archive tiers optional) | unknown/changing access patterns; auto-moves objects |
| **S3 Standard-IA** | ≥3 | 30 days | ms, per-GB fee | infrequently read, needs fast access |
| **S3 One Zone-IA** | 1 | 30 days | ms, per-GB fee | re-creatable data (loses data if the AZ is lost) |
| **S3 Express One Zone** | 1 | — | single-digit ms | latency-critical analytics/ML (directory buckets) |
| **Glacier Instant Retrieval** | ≥3 | 90 days | ms | archives read ~quarterly |
| **Glacier Flexible Retrieval** | ≥3 | 90 days | minutes–hours | backups |
| **Glacier Deep Archive** | ≥3 | 180 days | ≤12–48 h | compliance archives; cheapest |

Task 1's lifecycle config reported `"TransitionDefaultMinimumObjectSize": "all_storage_classes_128K"`. By default, lifecycle *transitions* skip objects smaller than 128 KB, because per-object overhead makes moving tiny objects cost more than it saves.

---

## Versioning

With versioning **Enabled**, every PUT creates a new version and a DELETE only adds a **delete marker**. Older versions stay recoverable, which protects against accidental overwrite or deletion and ransomware. A bucket's versioning state is *Unversioned → Enabled ⇄ Suspended*; it can never go back to unversioned.

Real result from Task 1, writing `notes.txt` twice:

```
+----------+------------+-------+-------------------------------------+
| IsLatest |    Key     | Size  |              VersionId              |
+----------+------------+-------+-------------------------------------+
|  True    |  notes.txt |  3    |  MTK2o2yK1wR72oGmVpKbS9XPBBxAcQD9   |
|  False   |  notes.txt |  3    |  dTS0x25rwm8om6ogKHORvg0hAbPxjCMU   |
+----------+------------+-------+-------------------------------------+
```

Each version is billed. Versioning without a lifecycle rule grows storage forever, which is why Task 1 pairs the two. Versioning is also required for **replication** (CRR/SRR) and **Object Lock**. **MFA Delete** (`mfa_delete = "Disabled"` in Task 1's state) can additionally require MFA to delete versions.

---

## Lifecycle policies

Rules that S3 runs automatically (asynchronously, about once a day) on objects matching a filter (prefix and/or tags and/or size):

- **Transition** actions move objects to a cheaper class after N days (e.g. Standard → Standard-IA at 30 d → Glacier at 90 d).
- **Expiration** actions delete current objects after N days, delete **noncurrent versions** N days after they are overwritten, remove expired delete markers, and **abort incomplete multipart uploads**.

Task 1's rule, read back from AWS:

```
"Rules": [
    {
        "ID": "expire-noncurrent-versions",
        "Filter": { "Prefix": "" },
        "Status": "Enabled",
        "NoncurrentVersionExpiration": { "NoncurrentDays": 30 },
        "AbortIncompleteMultipartUpload": { "DaysAfterInitiation": 7 }
    }
]
```

So the `v1` above would be deleted 30 days after `v2` replaced it, and failed multipart uploads, which are invisible in `aws s3 ls` but still billed, are cleaned up after 7 days.

---

## Encryption

**In transit:** HTTPS (TLS). A bucket policy with `"aws:SecureTransport": "false"` → Deny enforces it.

**At rest**, server-side:

| Mode | Keys managed by | Notes |
| --- | --- | --- |
| **SSE-S3** (`AES256`) | S3 | default for all new objects since Jan 2023. Free. |
| **SSE-KMS** (`aws:kms`) | AWS KMS key (AWS-managed or customer-managed) | key-policy access control + CloudTrail audit of every decrypt. Enable **S3 Bucket Keys** to cut KMS request cost. |
| **DSSE-KMS** | KMS, two layers | compliance workloads |
| **SSE-C** | you send the key with every request | now **blocked by default** on new buckets |

Client-side encryption (encrypting before upload) is the alternative when even AWS must not see plaintext.

Evidence from Task 1. The bucket default was SSE-S3, SSE-C appeared as blocked without being configured, and an object uploaded with no encryption flags came back encrypted:

```
"ApplyServerSideEncryptionByDefault": { "SSEAlgorithm": "AES256" },
"BlockedEncryptionTypes": { "EncryptionType": [ "SSE-C" ] }
...
$ aws s3api head-object --bucket saptak-tf-s3-demo-b53eac94 --key notes.txt --query '{SSE:ServerSideEncryption,Version:VersionId}'
{
    "SSE": "AES256",
    "Version": "MTK2o2yK1wR72oGmVpKbS9XPBBxAcQD9"
}
```

---

## Bucket policies and access control

S3 access is decided by several layers. **All buckets are private by default.**

| Layer | What it is |
| --- | --- |
| **Block Public Access** (account and bucket) | a guard-rail that overrides any policy or ACL that would make data public. All four flags on in both labs. |
| **Bucket policy** | a *resource-based* JSON policy on the bucket, with a `Principal`. Use it for cross-account access, forcing TLS or encryption, restricting to a VPC endpoint, or public website hosting. |
| **IAM identity policy** | what a user or role may do. Same-account access only needs this *or* the bucket policy to allow. |
| **ACLs** | legacy. Disabled by default on new buckets (Object Ownership = *Bucket owner enforced*). Task 1's state shows the single owner `FULL_CONTROL` grant. |
| **Pre-signed URLs** | time-limited access to one object without credentials |

Example bucket policy (enforce TLS):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyInsecureTransport",
    "Effect": "Deny",
    "Principal": "*",
    "Action": "s3:*",
    "Resource": ["arn:aws:s3:::BUCKET", "arn:aws:s3:::BUCKET/*"],
    "Condition": { "Bool": { "aws:SecureTransport": "false" } }
  }]
}
```

Session 19 used the identity-policy route instead. The bucket stayed fully private, and only the EC2 role could `s3:GetObject` under `site/*`. An anonymous request for the same object was refused:

```
$ curl -s -o /dev/null -w '%{http_code}\n' https://sst-s19-cloud-tf-site-c84c1873.s3.ap-south-1.amazonaws.com/site/index.html
403
```

---

## Common use cases

- **Static assets and websites** (usually behind CloudFront with Origin Access Control).
- **Backups, archives, and DR copies** (with lifecycle to Glacier and cross-region replication).
- **Data lakes and analytics**: Athena, EMR, Redshift Spectrum query objects in place, often in Parquet.
- **Logs**: CloudTrail, ALB, VPC Flow Logs, S3 access logs.
- **Build and deploy artifacts**: CI outputs, Lambda zips, container image layers (ECR stores them in S3), and Terraform **remote state** (S3 backend with `use_lockfile = true`).
- **Application uploads**: user images and documents via pre-signed URLs.

**Screenshot:** ![S3 versioning and encryption evidence](../../screenshots/07-s3-verify-cli.png)
