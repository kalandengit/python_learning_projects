# AI School Assistant — infrastructure as code (skeleton).
#
# M0 establishes the Terraform layout; real resources land when the first
# cloud environment is provisioned (pre-pilot, Milestone 6). Target shape per
# docs/04_ARCHITECTURE.md: one region, managed Postgres + Redis, object
# storage, app runtime (Fly.io / Railway / ECS — decided in ADR-0002 at
# provisioning time), secrets manager.

terraform {
  required_version = ">= 1.7"

  # Remote state backend is configured per environment at provisioning time:
  # backend "s3" { ... }
}

variable "environment" {
  description = "Deployment environment (staging | prod)"
  type        = string
}
