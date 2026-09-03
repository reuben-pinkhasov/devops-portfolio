resource "terraform_data" "app_image" {
  triggers_replace = [
    aws_ecr_repository.app.id
  ]

  provisioner "local-exec" {
    working_dir = "${path.module}/.."

    interpreter = ["/bin/bash", "-c"]

    command = <<-EOT
      set -e

      echo "Logging in to Amazon ECR..."

      aws ecr get-login-password \
        --region ${var.aws_region} |
        docker login \
        --username AWS \
        --password-stdin ${aws_ecr_repository.app.repository_url}

      echo "Building application image..."

      docker build \
        -t ${aws_ecr_repository.app.repository_url}:1.0 \
        ./app

      echo "Pushing application image..."

      docker push \
        ${aws_ecr_repository.app.repository_url}:1.0

      echo "Application image successfully pushed."
    EOT
  }

  depends_on = [
    aws_ecr_repository.app
  ]
}
