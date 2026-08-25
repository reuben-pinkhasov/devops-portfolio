# IAM role used by GitHub Actions CD through OIDC.
# This role is trusted only by the main branch.
resource "aws_iam_role" "github_actions_cd" {
  name = "devops-portfolio-github-actions-cd-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }

        Action = "sts:AssumeRoleWithWebIdentity"

        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
            "token.actions.githubusercontent.com:sub" = "repo:reuben-pinkhasov@308845402/devops-portfolio@1344991300:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

# Allow GitHub Actions to retrieve EKS cluster information
# when configuring kubectl.
resource "aws_iam_role_policy" "github_actions_cd_eks" {
  name = "devops-portfolio-github-actions-cd-eks"
  role = aws_iam_role.github_actions_cd.id

  policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Action = [
          "eks:DescribeCluster"
        ]

        Resource = aws_eks_cluster.main.arn
      }
    ]
  })
}

# Register the GitHub Actions CD IAM role with EKS.
resource "aws_eks_access_entry" "github_actions_cd" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions_cd.arn
  type          = "STANDARD"

  depends_on = [
    aws_eks_cluster.main
  ]
}

# Grant the GitHub Actions CD role administrator permissions
# within the devops-demo namespace only.
resource "aws_eks_access_policy_association" "github_actions_cd" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions_cd.arn

  policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"

  access_scope {
    type       = "namespace"
    namespaces = ["devops-demo"]
  }

  depends_on = [
    aws_eks_access_entry.github_actions_cd
  ]
}
