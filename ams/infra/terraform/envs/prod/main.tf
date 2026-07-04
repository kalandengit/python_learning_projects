# ------------------------------------------------------------------------------
# Production composition — West Europe primary (North Europe mirrors this file
# with location swapped; active-active per Section 14.3).
# State: Azure Storage backend with locking; apply only from CI (Section 12.6).
# ------------------------------------------------------------------------------

terraform {
  required_version = ">= 1.9"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.20"
    }
  }

  backend "azurerm" {
    resource_group_name  = "ams-tfstate-rg"
    storage_account_name = "amstfstateprod"
    container_name       = "tfstate"
    key                  = "prod.weu.tfstate"
    use_azuread_auth     = true
  }
}

provider "azurerm" {
  features {}
}

locals {
  location = "westeurope"
  suffix   = "weu-prod"
  tags = {
    project     = "ams"
    environment = "prod"
    managed_by  = "terraform"
    cost_center = "SEC-PLATFORM" # FinOps NFR-022
  }
}

resource "azurerm_resource_group" "ams" {
  name     = "ams-${local.suffix}-rg"
  location = local.location
  tags     = local.tags
}

resource "azurerm_virtual_network" "ams" {
  name                = "ams-vnet-${local.suffix}"
  location            = local.location
  resource_group_name = azurerm_resource_group.ams.name
  address_space       = ["10.40.0.0/16"]
  tags                = local.tags
}

resource "azurerm_subnet" "aks" {
  name                 = "snet-aks"
  resource_group_name  = azurerm_resource_group.ams.name
  virtual_network_name = azurerm_virtual_network.ams.name
  address_prefixes     = ["10.40.0.0/20"]
}

resource "azurerm_subnet" "data" {
  name                 = "snet-data"
  resource_group_name  = azurerm_resource_group.ams.name
  virtual_network_name = azurerm_virtual_network.ams.name
  address_prefixes     = ["10.40.16.0/24"]

  delegation {
    name = "pg-flex"
    service_delegation {
      name    = "Microsoft.DBforPostgreSQL/flexibleServers"
      actions = ["Microsoft.Network/virtualNetworks/subnets/join/action"]
    }
  }
}

resource "azurerm_subnet" "endpoints" {
  name                 = "snet-endpoints"
  resource_group_name  = azurerm_resource_group.ams.name
  virtual_network_name = azurerm_virtual_network.ams.name
  address_prefixes     = ["10.40.17.0/24"]
}

resource "azurerm_private_dns_zone" "pg" {
  name                = "ams-prod.private.postgres.database.azure.com"
  resource_group_name = azurerm_resource_group.ams.name
  tags                = local.tags
}

resource "azurerm_private_dns_zone_virtual_network_link" "pg" {
  name                  = "pg-vnet-link"
  resource_group_name   = azurerm_resource_group.ams.name
  private_dns_zone_name = azurerm_private_dns_zone.pg.name
  virtual_network_id    = azurerm_virtual_network.ams.id
}

module "aks" {
  source                 = "../../modules/aks"
  name                   = "ams-aks-${local.suffix}"
  location               = local.location
  resource_group_name    = azurerm_resource_group.ams.name
  subnet_id              = azurerm_subnet.aks.id
  user_pool_min          = 4
  user_pool_max          = 24 # Section 14.2 burst ceiling
  admin_group_object_ids = var.aks_admin_group_object_ids
  tags                   = local.tags
}

module "postgresql" {
  source              = "../../modules/postgresql"
  name                = "ams-pg-${local.suffix}"
  location            = local.location
  resource_group_name = azurerm_resource_group.ams.name
  delegated_subnet_id = azurerm_subnet.data.id
  private_dns_zone_id = azurerm_private_dns_zone.pg.id
  tags                = local.tags

  depends_on = [azurerm_private_dns_zone_virtual_network_link.pg]
}

module "redis" {
  source              = "../../modules/redis"
  name                = "ams-redis-${local.suffix}"
  location            = local.location
  resource_group_name = azurerm_resource_group.ams.name
  capacity            = 2
  subnet_id           = azurerm_subnet.endpoints.id
  tags                = local.tags
}

# WORM audit archive (Section 7.5): immutable container with a time-based
# retention policy — the blob-side half of the FR-048 control.
resource "azurerm_storage_account" "audit" {
  name                            = "amsauditworm${replace(local.suffix, "-", "")}"
  location                        = local.location
  resource_group_name             = azurerm_resource_group.ams.name
  account_tier                    = "Standard"
  account_replication_type        = "RAGZRS"
  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false
  tags                            = local.tags
}

resource "azurerm_storage_container" "audit" {
  name               = "audit-worm"
  storage_account_id = azurerm_storage_account.audit.id
}

resource "azurerm_storage_container_immutability_policy" "audit" {
  storage_container_resource_manager_id = azurerm_storage_container.audit.resource_manager_id
  immutability_period_in_days           = 2557 # 7 years (Section 7.4)
  protected_append_writes_enabled       = true
}

variable "aks_admin_group_object_ids" {
  type    = list(string)
  default = []
}

output "aks_oidc_issuer" {
  value = module.aks.oidc_issuer_url
}

output "postgres_fqdn" {
  value = module.postgresql.server_fqdn
}

output "redis_hostname" {
  value = module.redis.hostname
}

# VERIFY: storage account names are globally unique — adjust "amsauditworm..." if taken; immutability policy must be locked manually after validation (irreversible).
