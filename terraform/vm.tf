resource "yandex_compute_instance" "coinbase_vm" {
  name        = var.vm_instance_name
  platform_id = "standard-v3"
  zone        = var.zone

  resources {
    cores  = var.vm_resources.cores
    memory = var.vm_resources.memory
  }

  boot_disk {
    initialize_params {
      image_id = "fd83u9thmahrv9lgedrk" # Ubuntu 22.04 LTS
      size     = var.vm_resources.disk
      type     = "network-ssd"
    }
  }

  network_interface {
    subnet_id      = yandex_vpc_subnet.coinbase_subnet.id
    nat            = true
    security_group_ids = [yandex_vpc_security_group.vm_sg.id]
  }

  metadata = {
    ssh-keys = "${var.vm_user}:${file(var.ssh_public_key_path)}"
    user-data = templatefile("${path.module}/user_data.tpl", {
      clickhouse_host = yandex_mdb_clickhouse_cluster.coinbase_clickhouse.host[0].fqdn
      clickhouse_user = var.clickhouse_user
      clickhouse_password = var.clickhouse_password
    })
  }
}

resource "yandex_vpc_security_group" "vm_sg" {
  name        = "vm-security-group"
  description = "Security group for VM instance"
  network_id  = yandex_vpc_network.coinbase_network.id

  ingress {
    protocol       = "TCP"
    description    = "SSH access"
    port           = 22
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "Redpanda"
    port           = 9092
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "Redpanda Console"
    port           = 8080
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "Grafana"
    port           = 3000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
} 