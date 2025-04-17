variable "folder_id" {
  description = "Yandex Cloud Folder ID"
  type        = string
}

variable "cloud_id" {
  description = "Yandex Cloud ID"
  type        = string
}

variable "service_account_key_file" {
  description = "Path to service account key file"
  type        = string
  default     = "key.json"
}

variable "zone" {
  description = "Yandex Cloud Zone"
  type        = string
  default     = "ru-central1-a"
}

variable "clickhouse_user" {
  description = "ClickHouse username"
  type        = string
  default     = "admin"
}

variable "clickhouse_password" {
  description = "ClickHouse password"
  type        = string
  sensitive   = true
}

variable "vm_user" {
  description = "VM username for SSH access"
  type        = string
  default     = "ubuntu"
}

variable "ssh_public_key_path" {
  description = "Path to SSH public key for VM access"
  type        = string
  default     = "~/.ssh/id_rsa.pub"
}

variable "vm_instance_name" {
  description = "Name for the VM instance"
  type        = string
  default     = "coinbase-analytics-instance"
}

variable "vm_resources" {
  description = "VM resource configuration"
  type = object({
    cores  = number
    memory = number
    disk   = number
  })
  default = {
    cores  = 4
    memory = 8
    disk   = 30
  }
} 