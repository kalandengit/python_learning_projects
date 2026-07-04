variable "name" {
  description = "Cluster name, e.g. ams-aks-weu-prod"
  type        = string
}

variable "location" {
  description = "Azure region (westeurope / northeurope)"
  type        = string
}

variable "resource_group_name" {
  type = string
}

variable "kubernetes_version" {
  description = "AKS version (>=1.30 per platform standard)"
  type        = string
  default     = "1.31"
}

variable "sku_tier" {
  description = "Free | Standard | Premium — Standard+ for prod SLA"
  type        = string
  default     = "Standard"
}

variable "subnet_id" {
  type = string
}

variable "system_vm_size" {
  type    = string
  default = "Standard_D4ds_v5"
}

variable "user_vm_size" {
  type    = string
  default = "Standard_D8ds_v5"
}

variable "user_pool_min" {
  type    = number
  default = 3
}

variable "user_pool_max" {
  type    = number
  default = 12
}

variable "admin_group_object_ids" {
  description = "Entra group object IDs granted Azure RBAC cluster admin (PIM-eligible)"
  type        = list(string)
  default     = []
}

variable "tags" {
  type    = map(string)
  default = {}
}

# VERIFY: VM sizes are illustrative assumptions — confirm regional availability and quota.
