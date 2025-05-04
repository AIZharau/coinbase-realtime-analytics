resource "yandex_vpc_network" "coinbase_network" {
  name        = "coinbase-network"
  description = "Network for Coinbase analytics pipeline"
}

resource "yandex_vpc_subnet" "coinbase_subnet" {
  name           = "coinbase-subnet"
  zone           = var.zone
  network_id     = yandex_vpc_network.coinbase_network.id
  v4_cidr_blocks = ["10.5.0.0/24"]
}

resource "yandex_iam_service_account" "coinbase_sa" {
  name        = "coinbase-service-account"
  description = "Service account for Coinbase analytics pipeline"
}

resource "yandex_resourcemanager_folder_iam_member" "sa_storage_editor" {
  folder_id  = var.folder_id
  role       = "storage.editor"
  member     = "serviceAccount:${yandex_iam_service_account.coinbase_sa.id}"
  depends_on = [yandex_iam_service_account.coinbase_sa]
}

resource "yandex_resourcemanager_folder_iam_member" "sa_compute_admin" {
  folder_id = var.folder_id
  role      = "compute.admin"
  member    = "serviceAccount:${yandex_iam_service_account.coinbase_sa.id}"
  depends_on = [yandex_iam_service_account.coinbase_sa]
} 