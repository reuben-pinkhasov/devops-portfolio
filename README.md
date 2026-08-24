# devops-portfolio/
│
├── app/
│   ├── src/
│   ├── tests/
│   ├── package.json
│   └── playwright.config.ts
│
├── Dockerfile
│
├── terraform/
│   ├── provider.tf
│   ├── variables.tf
│   ├── vpc.tf
│   ├── ecr.tf
│   ├── eks.tf
│   ├── outputs.tf
│   └── terraform.tfvars
│
├── helm/
│   └── myapp/
│       ├── Chart.yaml
│       ├── values.yaml
│       └── templates/
│           ├── deployment.yaml
│           ├── service.yaml
│           └── ingress.yaml
│
└── .github/
    └── workflows/
        └── ci-cd.yml

Pipeline:
Developer
   │
   ▼
git push
   │
   ▼
GitHub
   │
   ▼
GitHub Actions
   │
   ├── Checkout
   │
   ├── Install dependencies
   │
   ├── Playwright tests
   │       │
   │       └── PASS
   │
   ├── AWS authentication
   │
   ├── Docker build
   │
   ├── Docker push
   │       │
   │       ▼
   │      ECR
   │
   └── Helm upgrade/install
           │
           ▼
          EKS
           │
           ▼
        Pods

Developer WSL
     │
     ├── Linux Node.js
     ├── Linux npm
     └── Linux Playwright
              │
              ▼
        GitHub Actions
              │
              ├── Linux Node.js
              ├── Playwright
              └── Docker
