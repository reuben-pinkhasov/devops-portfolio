# ============================================================
# EKS Access for Monitoring EC2
# Allows Prometheus on the monitoring instance to read
# Kubernetes resources from the EKS cluster.
# ============================================================

# ------------------------------------------------------------
# EKS Access Entry
# ------------------------------------------------------------

resource "aws_eks_access_entry" "monitoring_ec2" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.monitoring_ec2.arn

  type = "STANDARD"

  depends_on = [
    aws_iam_role.monitoring_ec2
  ]
}

# ------------------------------------------------------------
# Read-only EKS access
# ------------------------------------------------------------

resource "aws_eks_access_policy_association" "monitoring_ec2" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.monitoring_ec2.arn

  policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [
    aws_eks_access_entry.monitoring_ec2
  ]
}
