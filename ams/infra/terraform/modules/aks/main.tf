# ------------------------------------------------------------------------------
# Reusable AKS module (ADR-010/ADR-011). System/user pool split, workload
# identity, Azure CNI + network policy (Zero Trust default-deny is applied via
# k8s NetworkPolicies on top), AZ spread, autoscaling.
# ------------------------------------------------------------------------------

resource "azurerm_kubernetes_cluster" "this" {
  name                = var.name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.name
  kubernetes_version  = var.kubernetes_version
  sku_tier            = var.sku_tier

  default_node_pool {
    name                 = "system"
    vm_size              = var.system_vm_size
    zones                = ["1", "2", "3"]
    auto_scaling_enabled = true
    min_count            = 3
    max_count            = 6
    vnet_subnet_id       = var.subnet_id
    only_critical_addons_enabled = true

    upgrade_settings {
      max_surge = "33%"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    network_policy      = "cilium"
    network_data_plane  = "cilium"
    load_balancer_sku   = "standard"
  }

  azure_active_directory_role_based_access_control {
    azure_rbac_enabled     = true
    admin_group_object_ids = var.admin_group_object_ids
  }

  monitor_metrics {} # managed Prometheus scraping

  maintenance_window_auto_upgrade {
    frequency   = "Weekly"
    interval    = 1
    duration    = 4
    day_of_week = "Sunday"
    start_time  = "02:00"
    utc_offset  = "+00:00"
  }

  automatic_upgrade_channel = "patch"

  tags = var.tags
}

resource "azurerm_kubernetes_cluster_node_pool" "user" {
  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.this.id
  vm_size               = var.user_vm_size
  zones                 = ["1", "2", "3"]
  auto_scaling_enabled  = true
  min_count             = var.user_pool_min
  max_count             = var.user_pool_max
  vnet_subnet_id        = var.subnet_id
  mode                  = "User"

  upgrade_settings {
    max_surge = "33%"
  }

  tags = var.tags
}

# VERIFY: azurerm provider 4.x renamed enable_auto_scaling -> auto_scaling_enabled; aligned to 4.x here.
