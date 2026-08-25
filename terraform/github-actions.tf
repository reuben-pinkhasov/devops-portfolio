# IAM role used by GitHub Actions through OIDC
resource "aws_iam_role" "github_actions" {
  name = "devops-portfolio-github-actions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Federated = "arn:aws:iam::949948071592:oidc-provider/token.actions.githubusercontent.com"
        }

        Action = "sts:AssumeRoleWithWebIdentity"

        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }

          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:reuben-pinkhasov/devops-portfolio:ref:refs/heads/dev"
          }
        }
      }
    ]
  })
}

