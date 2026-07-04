variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "pg_version" {
  type    = string
  default = "18"
}

variable "sku_name" {
  description = "e.g. GP_Standard_D4ds_v5 (illustrative assumption — size from Section 14 model)"
  type        = string
  default     = "GP_Standard_D4ds_v5"
}

variable "storage_mb" {
  type    = number
  default = 1048576 # 1 TiB
}

variable "delegated_subnet_id" {
  type = string
}

variable "private_dns_zone_id" {
  type = string
}

variable "service_databases" {
  description = "One database per service (DB-per-service)"
  type        = list(string)
  default = [
    "ams_identity", "ams_visitor", "ams_badge", "ams_access", "ams_approval",
    "ams_notification", "ams_audit", "ams_site", "ams_occupancy", "ams_reporting",
  ]
}

variable "tags" {
  type    = map(string)
  default = {}
}
