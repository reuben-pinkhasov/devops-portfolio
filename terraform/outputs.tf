output "ecr_repository_url" {
  value = aws_ecr_repository.app.repository_url
}
output "eks_cluster_name" {
  value = aws_eks_cluster.main.name
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}
output "monitoring_instance_id" {
  value = aws_instance.monitoring.id
}

output "monitoring_private_ip" {
  value = aws_instance.monitoring.private_ip
}

output "monitoring_public_dns" {
  value = aws_instance.monitoring.public_dns
}
