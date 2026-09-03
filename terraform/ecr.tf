resource "aws_ecr_repository" "app" {
  name                 = "devops-portfolio-app"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "devops-portfolio-app"
  }
}
