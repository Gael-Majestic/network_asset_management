# -------------------------------------------------------
# OUTPUTS
# These values are printed in your terminal after
# terraform apply finishes — you will need them to connect
# -------------------------------------------------------

output "vm_public_ip" {
  description = "Public IP address of your VM — use this to SSH and RDP"
  value       = aws_eip.dev_vm_eip.public_ip
}

output "ssh_command" {
  description = "Copy and run this command to SSH into your VM"
  value       = "ssh -i ~/.ssh/dev-vm-key ubuntu@${aws_eip.dev_vm_eip.public_ip}"
}

output "vscode_remote_host" {
  description = "Add this to your VS Code SSH config"
  value       = "ubuntu@${aws_eip.dev_vm_eip.public_ip}"
}
