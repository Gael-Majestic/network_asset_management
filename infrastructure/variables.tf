# -------------------------------------------------------
# VARIABLES
# These are the values you can change without touching main.tf
# -------------------------------------------------------

variable "aws_region" {
  description = "AWS region where the VM will be created"
  type        = string
  default     = "us-east-1" # Change this to your preferred region, e.g. "af-south-1" for Cape Town
}

variable "ubuntu_ami" {
  description = "Ubuntu Server 24.04 LTS AMI ID"
  type        = string
  # Ubuntu 24.04 LTS in us-east-1 (N. Virginia)
  # If you use a different region, find the correct AMI at:
  # https://cloud-images.ubuntu.com/locator/ec2/
  default = "ami-0ec10929233384c7f"
}

variable "admin_cidr" {
  description = "Your public IP address in CIDR form, e.g. 203.0.113.10/32. Only this address can reach SSH, RDP, the API port and pgAdmin."
  type        = string
}

variable "ssh_public_key_path" {
  description = "Path to the SSH public key uploaded to AWS"
  type        = string
  default     = "~/.ssh/dev-vm-key.pub"
}
