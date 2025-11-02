variable "project_id" {
  description = "GCP project ID where the cluster will be created"
  type        = string
}

variable "region" {
  description = "GCP region for the GKE cluster"
  type        = string
  default     = "us-central1"
}

variable "cluster_location" {
  description = "Region or zone where the GKE control plane and node pool will run"
  type        = string
  default     = null
}

variable "cluster_name" {
  description = "Name for the GKE cluster"
  type        = string
  default     = "housing-agent-cluster"
}

variable "subnet_cidr" {
  description = "Primary CIDR block for the GKE subnetwork"
  type        = string
  default     = "10.10.0.0/20"
}

variable "pod_cidr" {
  description = "Secondary CIDR for pod IP allocation"
  type        = string
  default     = "10.20.0.0/16"
}

variable "service_cidr" {
  description = "Secondary CIDR for service IP allocation"
  type        = string
  default     = "10.30.0.0/20"
}

variable "node_machine_type" {
  description = "Machine type to use for worker nodes"
  type        = string
  default     = "e2-standard-2"
}

variable "node_image_type" {
  description = "Image type for worker nodes (CentOS is not available for GKE)"
  type        = string
  default     = "UBUNTU_CONTAINERD"
}

variable "node_disk_size_gb" {
  description = "Boot disk size per node"
  type        = number
  default     = 50
}

variable "node_zones" {
  description = "Optional list of zones for the node pool"
  type        = list(string)
  default     = []
}

variable "release_channel" {
  description = "GKE release channel"
  type        = string
  default     = "REGULAR"
}
