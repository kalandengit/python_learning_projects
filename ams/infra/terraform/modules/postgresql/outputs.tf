output "server_id" {
  value = azurerm_postgresql_flexible_server.this.id
}

output "server_fqdn" {
  value = azurerm_postgresql_flexible_server.this.fqdn
}

output "database_names" {
  value = [for db in azurerm_postgresql_flexible_server_database.service : db.name]
}
