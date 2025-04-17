# Terraform Infrastructure for Coinbase Real-Time Analytics

This directory contains Terraform configurations to deploy the Coinbase Real-Time Analytics pipeline infrastructure to Yandex Cloud.

## Prerequisites

- Terraform installed (version >= 1.0.0)
- Yandex Cloud CLI installed and configured
- Service account with appropriate permissions in Yandex Cloud
- SSH key pair for VM access

## Architecture Overview

The infrastructure consists of:

1. **Network and subnet** in Yandex Cloud
2. **ClickHouse managed service** for data storage
3. **Virtual Machine** for running Redpanda, Producer, and Consumer
4. **S3 storage** for raw data
5. **Service account** with necessary permissions

### Cloud Architecture

In the cloud deployment:

- A single VM runs Redpanda as well as both Producer and Consumer services
- The Producer streams Coinbase market data into the local Redpanda instance
- The Consumer reads from Redpanda and writes to the managed ClickHouse service
- Raw data is stored in S3-compatible Object Storage
- All services are configured as systemd services for automatic startup

The services on the VM are set up to automatically start on boot:
- `redpanda.service` - Runs Redpanda in a Docker container
- `coinbase-producer.service` - Runs the Coinbase websocket client
- `coinbase-consumer.service` - Runs the ClickHouse data loader

## Setup Instructions

### 1. Service Account Setup

```bash
# Install YC CLI if not already installed
curl https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Login to Yandex Cloud
yc login

# Create a service account
yc iam service-account create --name terraform-account

# Grant necessary permissions
yc resource-manager folder add-access-binding --name default \
  --service-account-name terraform-account \
  --role editor

# Create and download service account key
yc iam key create --service-account-name terraform-account \
  --output key.json
```

### 2. Configure Environment Variables

Copy the template and fill in your Yandex Cloud details:

```bash
cp .env.template .env
```

Edit the `.env` file with your values:
- `TF_VAR_cloud_id`: Your Yandex Cloud ID
- `TF_VAR_folder_id`: Your Yandex Cloud folder ID
- `TF_VAR_clickhouse_password`: Password for ClickHouse admin user

Source the environment variables:

```bash
source .env
```

### 3. Initialize and Apply Terraform

```bash
# Initialize Terraform
terraform init

# Plan the deployment to verify resources
terraform plan

# Apply the configuration
terraform apply
```

### 4. Access Resources

After successful deployment, Terraform will output:
- ClickHouse host FQDN
- VM external IP
- S3 bucket details

You can SSH into the VM using:

```bash
ssh ubuntu@<vm_external_ip>
```

## Clean Up

To destroy all created resources:

```bash
terraform destroy
```

## Configuration Parameters

Adjust resources and configurations in `variables.tf` as needed. 