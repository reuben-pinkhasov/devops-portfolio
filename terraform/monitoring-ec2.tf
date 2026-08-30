# ============================================================
# Monitoring EC2
# Docker + Docker Compose + Prometheus + Grafana
# ============================================================

# ------------------------------------------------------------
# Latest Amazon Linux 2023 AMI
# ------------------------------------------------------------

data "aws_ssm_parameter" "amazon_linux_2023" {
  name = "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
}

# ------------------------------------------------------------
# Monitoring Security Group
# ------------------------------------------------------------

resource "aws_security_group" "monitoring" {
  name        = "devops-portfolio-monitoring-sg"
  description = "Security group for Prometheus and Grafana monitoring EC2"
  vpc_id      = aws_vpc.main.id

  # SSH
  # Temporary for demo purposes.
  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Grafana
  ingress {
    description = "Grafana"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Prometheus
  ingress {
    description = "Prometheus"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Outbound traffic
  egress {
    description = "Allow outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "devops-portfolio-monitoring-sg"
    ManagedBy   = "Terraform"
    Project     = "devops-portfolio"
    Environment = "dev"
  }
}

# ------------------------------------------------------------
# IAM Role for Monitoring EC2
# ------------------------------------------------------------

resource "aws_iam_role" "monitoring_ec2" {
  name = "devops-portfolio-monitoring-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [
      {
        Effect = "Allow"

        Principal = {
          Service = "ec2.amazonaws.com"
        }

        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "devops-portfolio-monitoring-ec2-role"
    ManagedBy   = "Terraform"
    Project     = "devops-portfolio"
    Environment = "dev"
  }
}

# ------------------------------------------------------------
# Allow SSM access
# ------------------------------------------------------------

resource "aws_iam_role_policy_attachment" "monitoring_ssm" {
  role       = aws_iam_role.monitoring_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# ------------------------------------------------------------
# Allow Monitoring EC2 to describe EKS cluster
# ------------------------------------------------------------

resource "aws_iam_role_policy" "monitoring_eks" {
  name = "devops-portfolio-monitoring-eks"
  role = aws_iam_role.monitoring_ec2.id

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

# ------------------------------------------------------------
# Instance Profile
# ------------------------------------------------------------

resource "aws_iam_instance_profile" "monitoring_ec2" {
  name = "devops-portfolio-monitoring-ec2-profile"
  role = aws_iam_role.monitoring_ec2.name
}

# ------------------------------------------------------------
# Monitoring EC2
# ------------------------------------------------------------

resource "aws_instance" "monitoring" {
  ami           = data.aws_ssm_parameter.amazon_linux_2023.value
  instance_type = "t3.micro"

  # Public subnet
  subnet_id = aws_subnet.private_a.id

  vpc_security_group_ids = [
    aws_security_group.monitoring.id
  ]

  iam_instance_profile = aws_iam_instance_profile.monitoring_ec2.name

  # Recreate the instance whenever user_data changes.
  user_data_replace_on_change = true

  user_data = <<-EOF
              #!/bin/bash

              set -eux

              # ==================================================
              # System update & Installation (Fixed Conflict)
              # ==================================================

              # Using --allowerasing handles the curl-minimal conflict gracefully
              dnf update -y --allowerasing
              dnf install -y docker --allowerasing

              systemctl enable docker
              systemctl start docker

              # Allow ec2-user to use Docker without sudo
              usermod -aG docker ec2-user

              # ==================================================
              # Docker Compose
              # ==================================================

              mkdir -p /usr/local/lib/docker/cli-plugins

              # Using the pre-installed minimal curl to fetch Compose
              curl -SL \
                https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
                -o /usr/local/lib/docker/cli-plugins/docker-compose

              chmod +x /usr/local/lib/docker/cli-plugins/docker-compose

              # ==================================================
              # Monitoring directories
              # ==================================================

              mkdir -p /opt/monitoring/prometheus
              mkdir -p /opt/monitoring/grafana

              # ==================================================
              # Prometheus configuration
              # ==================================================

              cat > /opt/monitoring/prometheus/prometheus.yml <<'PROMETHEUS_EOF'
              global:
                scrape_interval: 15s
                evaluation_interval: 15s

              scrape_configs:
                - job_name: "prometheus"
                  static_configs:
                    - targets:
                        - "prometheus:9090"
PROMETHEUS_EOF

              # ==================================================
              # Docker Compose File
              # ==================================================

              cat > /opt/monitoring/docker-compose.yml <<'COMPOSE_EOF'
              services:
                prometheus:
                  image: prom/prometheus:latest
                  container_name: prometheus
                  restart: unless-stopped
                  ports:
                    - "9090:9090"
                  volumes:
                    - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
                    - prometheus-data:/prometheus
                  command:
                    - "--config.file=/etc/prometheus/prometheus.yml"
                    - "--storage.tsdb.path=/prometheus"
                    - "--storage.tsdb.retention.time=2d"

                grafana:
                  image: grafana/grafana:latest
                  container_name: grafana
                  restart: unless-stopped
                  ports:
                    - "3000:3000"
                  volumes:
                    - grafana-data:/var/lib/grafana
                  depends_on:
                    - prometheus

              volumes:
                prometheus-data:
                grafana-data:
COMPOSE_EOF

              # Fix directory ownership so compose works smoothly
              chown -R ec2-user:ec2-user /opt/monitoring

              # ==================================================
              # Start monitoring stack (Fixed permission block)
              # ==================================================

              cd /opt/monitoring

              # We use sudo here because the script is running as root
              # and needs to bypass any un-reloaded user group delays
              docker compose pull
              docker compose up -d

              # ==================================================
              # SSM Agent
              # ==================================================

              systemctl enable amazon-ssm-agent
              systemctl start amazon-ssm-agent

              # ==================================================
              # Initialization marker
              # ==================================================

              echo "Monitoring EC2 initialization completed" > /opt/monitoring/init-status.txt
              echo "Docker and Compose ready" >> /opt/monitoring/init-status.txt
              echo "Prometheus and Grafana started" >> /opt/monitoring/init-status.txt
              EOF


  tags = {
    Name        = "devops-portfolio-monitoring"
    ManagedBy   = "Terraform"
    Project     = "devops-portfolio"
    Environment = "dev"
    Role        = "monitoring"
  }
}
