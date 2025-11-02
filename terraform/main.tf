locals {
  region                        = trimspace(var.region)
  cluster_location              = trimspace(coalesce(var.cluster_location, var.region))
  node_zones                    = [for zone in var.node_zones : trimspace(zone)]
  pods_secondary_range_name     = "${var.cluster_name}-pods"
  services_secondary_range_name = "${var.cluster_name}-services"
}

provider "google" {
  project = var.project_id
  region  = local.region
}

resource "google_project_service" "container" {
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

resource "google_compute_network" "primary" {
  name                    = "${var.cluster_name}-net"
  auto_create_subnetworks = false

  depends_on = [google_project_service.compute]
}

resource "google_compute_subnetwork" "primary" {
  name          = "${var.cluster_name}-subnet"
  ip_cidr_range = var.subnet_cidr
  region        = local.region
  network       = google_compute_network.primary.id

  secondary_ip_range {
    range_name    = local.pods_secondary_range_name
    ip_cidr_range = var.pod_cidr
  }

  secondary_ip_range {
    range_name    = local.services_secondary_range_name
    ip_cidr_range = var.service_cidr
  }
}

resource "google_service_account" "nodes" {
  account_id   = "${var.cluster_name}-nodes"
  display_name = "${var.cluster_name} node pool"
}

resource "google_container_cluster" "primary" {
  name     = var.cluster_name
  location = local.cluster_location

  network    = google_compute_network.primary.id
  subnetwork = google_compute_subnetwork.primary.id

  remove_default_node_pool = true
  initial_node_count       = 1

  networking_mode = "VPC_NATIVE"

  release_channel {
    channel = var.release_channel
  }

  ip_allocation_policy {
    cluster_secondary_range_name  = local.pods_secondary_range_name
    services_secondary_range_name = local.services_secondary_range_name
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = false
    }
  }

  depends_on = [
    google_project_service.container,
    google_project_service.compute
  ]
}

resource "google_container_node_pool" "primary_nodes" {
  name       = "${var.cluster_name}-pool"
  location   = local.cluster_location
  cluster    = google_container_cluster.primary.name
  node_count = 3
  node_config {
    machine_type = var.node_machine_type
    image_type   = var.node_image_type
    disk_size_gb = var.node_disk_size_gb

    service_account = google_service_account.nodes.email

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

    metadata = {
      disable-legacy-endpoints = "true"
    }

    labels = {
      role = "worker"
    }

    tags = [
      "${var.cluster_name}-worker"
    ]
  }

  node_locations = local.node_zones

  depends_on = [
    google_container_cluster.primary,
    google_service_account.nodes
  ]
}
