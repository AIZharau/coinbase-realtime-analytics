output "clickhouse_host" {
  description = "ClickHouse host FQDN"
  value       = yandex_mdb_clickhouse_cluster.coinbase_clickhouse.host[0].fqdn
}

output "vm_external_ip" {
  description = "Public IP address of the VM"
  value       = yandex_compute_instance.coinbase_vm.network_interface[0].nat_ip_address
}

output "s3_bucket_name" {
  description = "S3 bucket name for raw data"
  value       = yandex_storage_bucket.coinbase_raw_data.bucket
}

output "s3_access_key" {
  description = "S3 access key"
  value       = yandex_iam_service_account_static_access_key.sa_static_key.access_key
  sensitive   = true
}

output "s3_secret_key" {
  description = "S3 secret key"
  value       = yandex_iam_service_account_static_access_key.sa_static_key.secret_key
  sensitive   = true
} 