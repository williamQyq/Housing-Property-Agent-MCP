output "cluster_name" {
  description = "Name of the created GKE cluster"
  value       = google_container_cluster.primary.name
}

output "cluster_endpoint" {
  description = "GKE master endpoint"
  value       = google_container_cluster.primary.endpoint
}

output "cluster_ca_certificate" {
  description = "Base64 decoded cluster CA certificate"
  value       = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}

output "node_pool_id" {
  description = "ID of the worker node pool"
  value       = google_container_node_pool.primary_nodes.id
}
