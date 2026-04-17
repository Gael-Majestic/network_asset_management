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
