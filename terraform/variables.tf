variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "devops-portfolio"
}

variable "github_repository" {
  description = "GitHub repository in OWNER/REPOSITORY format"
  type        = string
  default     = "reuben-pinkhasov/devops-portfolio"
}

variable "github_repository_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "reuben-pinkhasov"
}

variable "github_repository_name" {
  description = "GitHub repository name"
  type        = string
  default     = "devops-portfolio"
}

variable "github_owner_id" {
  description = "GitHub immutable owner ID"
  type        = string
  default     = "308845402"
}

variable "github_repository_id" {
  description = "GitHub immutable repository ID"
  type        = string
  default     = "1344991300"
}
