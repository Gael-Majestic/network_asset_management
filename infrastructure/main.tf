terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# -------------------------------------------------------
# 1. PROVIDER — tells Terraform to use AWS in your region
# -------------------------------------------------------
provider "aws" {
  region = var.aws_region
}

# -------------------------------------------------------
# 2. KEY PAIR — your SSH key to access the VM
#    Run this ONCE before terraform apply:
#    ssh-keygen -t rsa -b 4096 -f ~/.ssh/dev-vm-key
# -------------------------------------------------------
resource "aws_key_pair" "dev_vm_key" {
  key_name   = "dev-vm-key"
  public_key = file("c:/Users/Hp/dev-vm-key.pub") # Change this path if your SSH key is stored elsewhere
}

# -------------------------------------------------------
# 3. SECURITY GROUP — firewall rules for the VM
# -------------------------------------------------------
resource "aws_security_group" "dev_vm_sg" {
  name        = "dev-vm-sg"
  description = "Allow SSH, HTTP, HTTPS and app ports"

  # SSH — to connect from your laptop
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTP
  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # FastAPI app port
  ingress {
    description = "FastAPI"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # pgAdmin (PostgreSQL GUI)
  ingress {
    description = "pgAdmin"
    from_port   = 5050
    to_port     = 5050
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # RDP — for GUI desktop access (XRDP)
  ingress {
    description = "RDP for GUI"
    from_port   = 3389
    to_port     = 3389
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow all outbound traffic (to install packages, pull images etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "dev-vm-sg"
  }
}

# -------------------------------------------------------
# 4. EC2 INSTANCE — the actual VM
# -------------------------------------------------------
resource "aws_instance" "dev_vm" {
  ami                    = var.ubuntu_ami
  instance_type          = "t3.large"
  key_name               = aws_key_pair.dev_vm_key.key_name
  vpc_security_group_ids = [aws_security_group.dev_vm_sg.id]

  # 50 GB SSD — enough for Ubuntu, Docker images, and your project
  root_block_device {
    volume_size           = 50
    volume_type           = "gp3"
    delete_on_termination = true
  }

  # This script runs automatically the FIRST TIME the VM boots.
  # It installs Docker, Docker Compose, and the XFCE desktop (GUI).
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Update system packages
    apt-get update -y
    apt-get upgrade -y

    # ---- Install Docker ----
    apt-get install -y ca-certificates curl gnupg
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt-get update -y
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

    # Allow ubuntu user to run Docker without sudo
    usermod -aG docker ubuntu

    # ---- Install XFCE Desktop (lightweight GUI) ----
    apt-get install -y xfce4 xfce4-goodies

    # ---- Install XRDP (lets you connect via Remote Desktop) ----
    apt-get install -y xrdp
    adduser xrdp ssl-cert
    echo "startxfce4" > /home/ubuntu/.xsession
    chown ubuntu:ubuntu /home/ubuntu/.xsession
    systemctl enable xrdp
    systemctl start xrdp

    # ---- Set password for ubuntu user (for RDP login) ----
    echo "ubuntu:ChangeMe123!" | chpasswd

    # ---- Install useful tools ----
    apt-get install -y git curl wget unzip vim tree htop net-tools

    # Done
    echo "Bootstrap complete" >> /var/log/user-data.log
  EOF

  tags = {
    Name        = "dev-vm"
    Project     = "network-asset-api"
    Environment = "dev"
  }
}

# -------------------------------------------------------
# 5. ELASTIC IP — gives your VM a fixed public IP address
#    so it does not change every time you start/stop it
# -------------------------------------------------------
resource "aws_eip" "dev_vm_eip" {
  instance = aws_instance.dev_vm.id
  domain   = "vpc"

  tags = {
    Name = "dev-vm-eip"
  }
}
