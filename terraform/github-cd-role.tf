resource "aws_iam_role" "github_actions_cd" {
  name = "${var.project_name}-github-actions-cd-role"

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

            "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:ref:refs/heads/main"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "github_actions_cd_eks" {
  name = "${var.project_name}-github-actions-cd-eks"
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
      },

      {
        Effect = "Allow"

        Action = [
          "ecr:DescribeImages"
        ]

        Resource = aws_ecr_repository.app.arn
      }
    ]
  })
}

resource "aws_eks_access_entry" "github_actions_cd" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions_cd.arn
  type          = "STANDARD"

  depends_on = [
    aws_eks_cluster.main
  ]
}

resource "aws_eks_access_policy_association" "github_actions_cd" {
  cluster_name  = aws_eks_cluster.main.name
  principal_arn = aws_iam_role.github_actions_cd.arn

  policy_arn = "arn:aws:eks::aws:cluster-access-policy/AmazonEKSAdminPolicy"

  access_scope {
    type = "namespace"

    namespaces = [
      "devops-demo"
    ]
  }

  depends_on = [
    aws_eks_access_entry.github_actions_cd
  ]
}
