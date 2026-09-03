resource "kubernetes_namespace_v1" "devops_demo" {
  metadata {
    name = "devops-demo"
  }

  depends_on = [
    aws_eks_node_group.main,
    aws_eks_access_policy_association.admin,
    terraform_data.app_image
  ]
}

resource "kubernetes_deployment_v1" "myapp" {
  metadata {
    name      = "myapp"
    namespace = kubernetes_namespace_v1.devops_demo.metadata[0].name
  }

  spec {
    replicas = 2

    selector {
      match_labels = {
        app = "myapp"
      }
    }

    template {
      metadata {
        labels = {
          app = "myapp"
        }
      }

      spec {
        container {
          name  = "myapp"
          image = "${aws_ecr_repository.app.repository_url}:1.0"

          port {
            container_port = 3000
          }
        }
      }
    }
  }

  depends_on = [
    aws_eks_node_group.main,
    aws_eks_access_policy_association.admin,
    terraform_data.app_image
  ]
}

resource "kubernetes_service_v1" "myapp" {
  metadata {
    name      = "myapp"
    namespace = kubernetes_namespace_v1.devops_demo.metadata[0].name
  }

  spec {
    selector = {
      app = "myapp"
    }

    port {
      port        = 80
      target_port = 3000
    }

    type = "ClusterIP"
  }

  depends_on = [
    kubernetes_deployment_v1.myapp
  ]
}

resource "kubernetes_ingress_v1" "myapp" {
  metadata {
    name      = "myapp"
    namespace = kubernetes_namespace_v1.devops_demo.metadata[0].name

    annotations = {
      "alb.ingress.kubernetes.io/scheme"      = "internet-facing"
      "alb.ingress.kubernetes.io/target-type" = "ip"
    }
  }

  spec {
    ingress_class_name = "alb"

    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service_v1.myapp.metadata[0].name

              port {
                number = 80
              }
            }
          }
        }
      }
    }
  }

  depends_on = [
    helm_release.aws_load_balancer_controller,
    kubernetes_service_v1.myapp
  ]
}
