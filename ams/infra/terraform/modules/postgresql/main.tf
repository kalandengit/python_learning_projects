# ------------------------------------------------------------------------------
# PostgreSQL Flexible Server module (ADR-006/ADR-T11). Zone-redundant HA,
# geo-redundant backup, one database per service (DB-per-service rule).
# ------------------------------------------------------------------------------

resource "azurerm_postgresql_flexible_server" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  version    = var.pg_version # "18" per ADR-T11; variable so the fallback path is one line
  sku_name   = var.sku_name
  storage_mb = var.storage_mb

  backup_retention_days        = 35
  geo_redundant_backup_enabled = true

  high_availability {
    mode                      = "ZoneRedundant"
    standby_availability_zone = "2"
  }

  authentication {
    active_directory_auth_enabled = true # Entra-integrated auth (PG18 also adds OAuth)
    password_auth_enabled         = false
  }

  delegated_subnet_id = var.delegated_subnet_id
  private_dns_zone_id = var.private_dns_zone_id

  maintenance_window {
    day_of_week  = 0
    start_hour   = 2
    start_minute = 0
  }

  tags = var.tags
}

# One isolated database per service (Section 6.2 matrix).
resource "azurerm_postgresql_flexible_server_database" "service" {
  for_each  = toset(var.service_databases)
  name      = each.value
  server_id = azurerm_postgresql_flexible_server.this.id
  charset   = "UTF8"
  collation = "en_US.utf8"
}

resource "azurerm_postgresql_flexible_server_configuration" "shared_preload" {
  name      = "shared_preload_libraries"
  server_id = azurerm_postgresql_flexible_server.this.id
  value     = "pg_cron,pg_stat_statements"
}

# VERIFY: PG 18 tier availability on Flexible Server in westeurope/northeurope at provisioning time (ADR-T11 fallback applies otherwise).
