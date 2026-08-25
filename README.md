>                                             # DevOps Portfolio — AWS EKS CI/CD Platform
## Live Application
The application is currently deployed to Amazon EKS and exposed through an AWS Application Load Balancer.
**Live URL:**  
http://k8s-devopsde-myapp-0856a5741a-527240915.us-east-1.elb.amazonaws.com/
> The URL is backed by an internet-facing AWS Application Load Balancer managed by the AWS Load Balancer Controller.

--------------------------------------------------------------

A hands-on DevOps project demonstrating how a containerized web application can be tested, built, stored, and deployed to Amazon EKS using GitHub Actions, AWS, Docker, Helm, Terraform, and Kubernetes.
The project demonstrates a production-style development workflow:

Developer
   │
   │ git push
   ▼
GitHub — dev
   │
   ▼
CI
   ├── Install dependencies
   ├── Install Playwright
   └── Run automated tests
   │
   │ Pull Request
   ▼
GitHub — main
   │
   ▼
CI
   ├── Automated tests
   ├── Configure AWS using OIDC
   ├── Build Docker image
   └── Push image to Amazon ECR
   │
   ▼
CD
   │
   ├── Deploy Docker image to Amazon EKS
   ├── Helm upgrade/install
   └── Verify Kubernetes rollout
   │
   ▼
AWS Load Balancer Controller
   │
   ▼
Internet-facing AWS ALB
   │
   ▼
Kubernetes Service
   │
   ▼
Application Pod

-----------------------------------------------------------------------------------------

Project Goals
The main goals of this project are to demonstrate practical DevOps and SRE skills rather than simply deploying an application.

The project covers:
Git-based development workflow
Pull Request based promotion from dev to main
Automated CI testing
Playwright browser testing
Docker image creation
Amazon ECR image registry
GitHub Actions → AWS authentication using OIDC
Kubernetes deployment on Amazon EKS
Helm-based application deployment
AWS Load Balancer Controller
Internet-facing Application Load Balancer
Terraform infrastructure provisioning
Kubernetes deployment verification
Separation of CI and CD responsibilities

-----------------------------------------------------------

AWS Architecture
                         Internet
                            │
                            ▼
                    ┌─────────────────┐
                    │   AWS ALB       │
                    │ Internet-facing │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ EKS Kubernetes  │
                    │                 │
                    │   Ingress       │
                    │      │          │
                    │      ▼          │
                    │   Service       │
                    │      │          │
                    │      ▼          │
                    │   Pod           │
                    │  myapp          │
                    └─────────────────┘
                             ▲
                             │
                       Docker image
                             │
                    ┌────────┴────────┐
                    │      ECR        │
                    │ Docker Registry │
                    └─────────────────┘

The application is deployed to Amazon EKS.
The Kubernetes Service remains ClusterIP, while the AWS Load Balancer Controller creates an internet-facing Application Load Balancer from the Kubernetes Ingress.
This means the Kubernetes worker nodes do not need to be directly exposed to the Internet.

----------------------------------------------------------------------------------------------------

CI/CD Workflow
Development workflow
Development takes place on the dev branch.
When code is pushed to dev, GitHub Actions runs the CI pipeline:

git push dev
      │
      ▼
GitHub Actions
      │
      ├── npm ci
      ├── Install Playwright
      └── Run Playwright tests

The development branch does not push production Docker images to ECR.
This allows developers to validate changes before promoting them to main.

----------------------------------------------------------------------------------

Pull Request workflow
Changes are promoted from dev to main through a Pull Request.

dev
 │
 │ Pull Request
 ▼
main
 │
 ▼
CI validation
 │
 ├── Playwright tests
 └── Other CI checks
 │
 ▼
Merge

The Pull Request acts as a quality gate before production deployment.

-------------------------------------------------------------------------------

Main branch CI
After the Pull Request is merged into main, the CI pipeline runs again.
On a successful main build:

main push
   │
   ▼
Playwright tests
   │
   ▼
AWS OIDC authentication
   │
   ▼
Amazon ECR login
   │
   ▼
Docker build
   │
   ▼
Docker push
   │
   ▼
ECR

The Docker image is tagged with the Git commit SHA.
Example:
949948071592.dkr.ecr.us-east-1.amazonaws.com/devops-portfolio-app:<commit-sha>
Using the commit SHA provides an immutable reference between source code, Docker image, and deployment.

---------------------------------------------------------------

Continuous Deployment
CD is responsible only for deploying an already-built image.
The CD workflow can be triggered manually from GitHub Actions.
This provides a deliberate separation:

CI
 │
 ├── Test
 ├── Build
 └── Push image to ECR
          │
          ▼
         ECR
          │
          │ manual CD trigger
          ▼
CD
 │
 ├── Authenticate to AWS
 ├── Configure kubectl
 ├── Install Helm
 ├── Deploy to EKS
 └── Verify rollout

The CD workflow verifies that the requested image exists in ECR before deployment.
It then deploys the image using Helm.

----------------------------------------
Kubernetes Deployment
The application is packaged as a Helm chart:

helm/
└── myapp/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── ingress.yaml
        ├── serviceaccount.yaml
        ├── hpa.yaml
        └── ...

Helm is used to manage the Kubernetes deployment.
The deployment specifies the Docker image:
ECR repository + Git commit SHA
For example:
devops-portfolio-app:4a39ff0b62ab232451704abc0528c22825d5473c
This allows the deployed Kubernetes workload to be directly traced back to a specific Git commit.

--------------------------------------------------------------------

AWS Load Balancer Controller
The project uses the AWS Load Balancer Controller to integrate Kubernetes Ingress with AWS Application Load Balancers.
The application is exposed through:

Internet
   │
   ▼
Internet-facing ALB
   │
   ▼
Kubernetes Ingress
   │
   ▼
ClusterIP Service
   │
   ▼
Application Pod

The ALB uses Kubernetes Ingress configuration to route traffic to the application.
The worker nodes themselves are not exposed through a public IP for application traffic.

--------------------------------------------------------------------

Infrastructure as Code

AWS infrastructure is managed using Terraform.
The Terraform configuration includes infrastructure and AWS integrations required by the application, including:
    Amazon VPC
    Amazon EKS
    EKS node infrastructure
    IAM roles
    GitHub Actions OIDC integration
    GitHub Actions IAM roles
    EKS OIDC configuration
    AWS Load Balancer Controller IAM configuration
    Required AWS policies
Terraform allows the environment to be recreated rather than manually configured.

Typical lifecycle:

terraform init
terraform plan
terraform apply
      │
      ▼
AWS infrastructure
      │
      ▼
EKS
      │
      ▼
Kubernetes deployment

The environment can also be removed with:
    terraform destroy
and recreated with Terraform.

------------------------------------------------------

Security

A key part of the project is avoiding long-lived AWS credentials inside GitHub Actions.
GitHub Actions authenticates to AWS using:

GitHub Actions
      │
      ▼
OIDC token
      │
      ▼
AWS IAM
      │
      ▼
Assumed IAM role

No permanent AWS access keys are required by the CI/CD workflow.
Separate IAM roles are used for GitHub Actions CI and CD operations.
The IAM roles are restricted to the GitHub repository/workflow context.

-------------------------------------------------------------------------------------------------------------------

Technologies

Area	                                Technologies
Cloud	                                AWS
Infrastructure	                        Terraform
Containers	                            Docker
Container Registry	                    Amazon ECR
Kubernetes	                            Amazon EKS
Package Management	                    Helm
Load Balancing	                        AWS Application Load Balancer
Kubernetes Integration	                AWS Load Balancer Controller
CI/CD	                                GitHub Actions
Authentication	                        GitHub OIDC + AWS IAM
Testing	                                Playwright
Application	                            Node.js
Version Control	                        Git / GitHub
Scripting	                            Bash
Monitoring/Operations	                Kubernetes CLI, AWS CLI 

-----------------------------------------------------------------------------

Repository Structure
.
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
│
├── app/
│   ├── package.json
│   ├── package-lock.json
│   └── ...
│
├── helm/
│   └── myapp/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│
├── terraform/
│   ├── eks.tf
│   ├── eks-oidc.tf
│   ├── github-actions.tf
│   ├── github-cd-role.tf
│   ├── alb-controller-iam.tf
│   ├── alb-controller-policy.json
│   ├── provider.tf
│   └── ...
│
└── README.md

--------------------------------------------------------------------------

Key DevOps Practices Demonstrated
1. Shift-left testing
Automated Playwright tests run before code is promoted to the production branch.

2. Branch-based promotion
dev → Pull Request → main
Production image creation happens only after code reaches main and passed CI.

3. Immutable Docker releases
Images are tagged using Git commit SHA rather than relying only on mutable tags such as latest.

4. Infrastructure as Code
AWS infrastructure is provisioned and managed with Terraform.

5. Secure cloud authentication
GitHub Actions uses AWS OIDC instead of storing long-lived AWS credentials.

6. Kubernetes deployment automation
Helm provides repeatable application deployments to EKS.

7. Cloud-native load balancing
AWS Load Balancer Controller integrates Kubernetes Ingress with AWS ALB.

8. Deployment verification
CD verifies the Kubernetes rollout after deployment:
kubectl rollout status
and displays the image currently deployed.

------------------------------------------------------------------------

Example End-to-End Release
A typical release looks like:

1. Developer changes application
             │
             ▼
2. Push to dev
             │
             ▼
3. Playwright CI
             │
             ▼
4. Pull Request to main
             │
             ▼
5. PR CI validation
             │
             ▼
6. Merge PR
             │
             ▼
7. CI runs on main
             │
             ├── Playwright
             ├── Docker build
             └── ECR push
                     │
                     ▼
8. CD triggered manually
             │
             ▼
9. Helm deploys image to EKS
             │
             ▼
10. Kubernetes rollout verification
             │
             ▼
11. Application available through AWS ALB

--------------------------------------------------------------------------------------------------

What This Project Demonstrates
This project is designed to demonstrate practical experience with the complete application delivery lifecycle:
Source Code → Testing → Containerization → Registry → Cloud Authentication → Kubernetes → Load Balancer → Deployment Verification
It focuses on implementing the infrastructure and delivery pipeline rather than using a fully managed CI/CD abstraction.
The result is a reproducible AWS environment where infrastructure is defined with Terraform, applications are packaged with Docker and Helm, CI/CD is implemented with GitHub Actions, and workloads run on Amazon EKS.
