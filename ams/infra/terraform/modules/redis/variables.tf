variable "name" {
  type = string
}

variable "location" {
  type = string
}

variable "resource_group_name" {
  type = string
}

variable "capacity" {
  description = "Premium P-family capacity (1 = P1 6 GB)"
  type        = number
  default     = 1
}

variable "subnet_id" {
  description = "Subnet for the private endpoint"
  type        = string
}

variable "tags" {
  type    = map(string)
  default = {}
}
