# ============================================================
# FULL SETUP GUIDE — Dev VM on AWS with Terraform
# ============================================================


# ============================================================
# STEP 1 — BEFORE YOU RUN TERRAFORM
# ============================================================

# 1a. Install Terraform on your laptop
#     Download from: https://developer.hashicorp.com/terraform/install
#     Verify install:
terraform -version

# 1b. Configure your AWS credentials on your laptop
#     (Get these from AWS Console → IAM → Your user → Security credentials)
aws configure
# It will ask for:
#   AWS Access Key ID
#   AWS Secret Access Key
#   Default region: af-south-1
#   Default output format: json

# 1c. Generate your SSH key pair (run once, saves to ~/.ssh/)
ssh-keygen -t rsa -b 4096 -f ~/.ssh/dev-vm-key
# Press Enter twice to skip passphrase (or add one for security)
# This creates two files:
#   ~/.ssh/dev-vm-key       ← private key (NEVER share this)
#   ~/.ssh/dev-vm-key.pub   ← public key (Terraform uploads this to AWS)


# ============================================================
# STEP 2 — FIND YOUR UBUNTU AMI FOR YOUR REGION
# ============================================================
# The AMI ID in variables.tf must match your region.
# Go to: https://cloud-images.ubuntu.com/locator/ec2/
# Filter: Region=af-south-1, Version=24.04, Arch=amd64, Instance=hvm:ebs
# Copy the AMI ID and paste it into variables.tf


# ============================================================
# STEP 3 — RUN TERRAFORM
# ============================================================

# Go into the Terraform folder
cd infrastructure

# Initialise Terraform (downloads the AWS provider)
terraform init

# Preview what Terraform will create (nothing is created yet)
terraform plan

# Create the VM (type "yes" when prompted). admin_cidr is your own public IP:
# only that address can reach SSH, RDP and the API port.
terraform apply -var "admin_cidr=$(curl -s https://checkip.amazonaws.com)/32"

# When done, Terraform prints your VM's public IP and SSH command.


# ============================================================
# STEP 4 — WAIT FOR THE VM TO FINISH BOOTING
# ============================================================
# The user_data script (Docker + GUI install) takes about 5-8 minutes.
# You can SSH in immediately, but Docker may not be ready yet.
# Check the bootstrap log:
ssh -i ~/.ssh/dev-vm-key ubuntu@YOUR_VM_IP
cat /var/log/user-data.log
# When you see "Bootstrap complete" — everything is installed.


# ============================================================
# STEP 5 — CONNECT VS CODE TO YOUR VM (Remote SSH)
# ============================================================

# 5a. Install the "Remote - SSH" extension in VS Code
#     Open VS Code → Extensions (Ctrl+Shift+X) → search "Remote - SSH" → Install

# 5b. Add your VM to VS Code SSH config
#     Press Ctrl+Shift+P → type "Remote-SSH: Open SSH Configuration File"
#     Select: ~/.ssh/config
#     Add these lines (replace YOUR_VM_IP with the IP from terraform output):

# Host dev-vm
#     HostName YOUR_VM_IP
#     User ubuntu
#     IdentityFile ~/.ssh/dev-vm-key

# 5c. Connect
#     Press Ctrl+Shift+P → "Remote-SSH: Connect to Host" → select "dev-vm"
#     VS Code opens a new window — you are now INSIDE the VM.
#     Any file you create, any terminal you open = it's on the VM, not your laptop.


# ============================================================
# STEP 6 — CONNECT TO THE GUI (Remote Desktop)
# ============================================================

# On Windows:
#   Open "Remote Desktop Connection" (built into Windows)
#   Computer: YOUR_VM_IP
#   Username: ubuntu
#   Password: the one you set after your first SSH login with `sudo passwd ubuntu`

# On Mac:
#   Install "Microsoft Remote Desktop" from the App Store
#   Add a new PC: YOUR_VM_IP
#   Username: ubuntu / Password: the one you set with `sudo passwd ubuntu`

# You will see the XFCE desktop — a full Linux GUI.
# Use this to explore the file manager, terminal, and settings visually.


# ============================================================
# STEP 7 — RUN THE API ON THE VM
# ============================================================
# On the VM (SSH or the VS Code terminal):
git clone https://github.com/Gael-Majestic/network_asset_management.git
cd network_asset_management
cp .env.example .env        # then edit .env: passwords and SECRET_KEY
docker compose up -d --build
curl http://localhost:8000/health/ready

# From your laptop, the API is at http://YOUR_VM_IP:8000/docs
# (the security group allows port 8000 from admin_cidr only).

# pgAdmin listens on the VM's localhost only. Start it, then open an
# SSH tunnel from your laptop and browse to http://localhost:5050
docker compose --profile tools up -d                       # on the VM
ssh -i ~/.ssh/dev-vm-key -L 5050:localhost:5050 ubuntu@YOUR_VM_IP   # on your laptop


# ============================================================
# STEP 8 — STOP THE VM WHEN DONE (IMPORTANT — SAVES MONEY)
# ============================================================

# Option A: AWS Console → EC2 → Instances → select your VM → Instance State → Stop
# Option B: Via AWS CLI:
aws ec2 stop-instances --instance-ids YOUR_INSTANCE_ID --region af-south-1

# To start it again:
aws ec2 start-instances --instance-ids YOUR_INSTANCE_ID --region af-south-1

# NOTE: The Elastic IP keeps your public IP the same after stop/start.
# You will NOT be charged for the VM's compute while it is stopped.
# You WILL still pay for its disk (EBS) and for the Elastic IP: AWS charges
# about $0.005/hour for every public IPv4 address, running or stopped.


# ============================================================
# STEP 9 — DESTROY EVERYTHING WHEN NO LONGER NEEDED
# ============================================================
# WARNING: This deletes the VM and all data on it permanently.
terraform destroy
