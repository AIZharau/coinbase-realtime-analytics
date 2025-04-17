resource "yandex_mdb_clickhouse_cluster" "coinbase_clickhouse" {
  name               = "coinbase-clickhouse"
  environment        = "PRODUCTION"
  network_id         = yandex_vpc_network.coinbase_network.id
  security_group_ids = [yandex_vpc_security_group.clickhouse_sg.id]
  
  clickhouse {
    resources {
      resource_preset_id = "s2.micro"
      disk_type_id       = "network-ssd"
      disk_size          = 20
    }
  }

  host {
    type             = "CLICKHOUSE"
    zone             = var.zone
    subnet_id        = yandex_vpc_subnet.coinbase_subnet.id
    assign_public_ip = true
  }

  database {
    name = "coinbase_market_data"
  }

  user {
    name     = var.clickhouse_user
    password = var.clickhouse_password
    permission {
      database_name = "coinbase_market_data"
    }
  }

  maintenance_window {
    type = "ANYTIME"
  }
}

resource "yandex_vpc_security_group" "clickhouse_sg" {
  name        = "clickhouse-security-group"
  description = "Security group for ClickHouse cluster"
  network_id  = yandex_vpc_network.coinbase_network.id

  ingress {
    protocol       = "TCP"
    description    = "ClickHouse HTTP"
    port           = 8123
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    protocol       = "TCP"
    description    = "ClickHouse Native Protocol"
    port           = 9000
    v4_cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    protocol       = "ANY"
    description    = "Allow all outgoing traffic"
    v4_cidr_blocks = ["0.0.0.0/0"]
  }
} 