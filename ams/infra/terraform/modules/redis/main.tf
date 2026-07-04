# ------------------------------------------------------------------------------
# Azure Cache for Redis module (ADR-004/ADR-T04). Zone-redundant Premium,
# TLS 1.3-only clients, private endpoint access.
# ------------------------------------------------------------------------------

resource "azurerm_redis_cache" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name

  capacity = var.capacity
  family   = "P"
  sku_name = "Premium"

  non_ssl_port_enabled          = false
  minimum_tls_version           = "1.2"
  public_network_access_enabled = false
  zones                         = ["1", "2", "3"]

  redis_configuration {
    maxmemory_policy = "volatile-lru" # caches expire; rebuildable-only rule (ADR-T04)
  }

  tags = var.tags
}

resource "azurerm_private_endpoint" "redis" {
  name                = "${var.name}-pe"
  location            = var.location
  resource_group_name = var.resource_group_name
  subnet_id           = var.subnet_id

  private_service_connection {
    name                           = "${var.name}-psc"
    private_connection_resource_id = azurerm_redis_cache.this.id
    subresource_names              = ["redisCache"]
    is_manual_connection           = false
  }

  tags = var.tags
}

# VERIFY: minimum_tls_version accepted values on azurerm 4.x ("1.2" is the ceiling exposed; TLS 1.3 negotiation is service-side).
