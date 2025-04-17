terraform {
  required_providers {
    yandex = {
      source  = "yandex-cloud/yandex"
      version = "~> 0.92.0"
    }
  }
  required_version = ">= 1.0.0"
}

provider "yandex" {
  folder_id                = var.folder_id
  cloud_id                 = var.cloud_id
  service_account_key_file = var.service_account_key_file
  zone                     = var.zone
} 