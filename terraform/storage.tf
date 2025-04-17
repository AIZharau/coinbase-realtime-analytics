resource "yandex_storage_bucket" "coinbase_raw_data" {
  bucket     = "coinbase-raw-data"
  acl        = "private"
  max_size   = 1073741824 # 1GB
  access_key = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  secret_key = yandex_iam_service_account_static_access_key.sa_static_key.secret_key

  lifecycle_rule {
    id      = "cleanup-old-data"
    enabled = true

    expiration {
      days = 30
    }
  }
}

resource "yandex_iam_service_account_static_access_key" "sa_static_key" {
  service_account_id = yandex_iam_service_account.coinbase_sa.id
  description        = "Static access key for S3 storage"
} 