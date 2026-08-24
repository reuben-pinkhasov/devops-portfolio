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

devops-portfolio/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── app/
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── server.js
│   └── tests/
│
├── helm/
│   └── myapp/
│
├── terraform/
│   ├── provider.tf
│   ├── vpc.tf
│   ├── ecr.tf
│   ├── eks.tf
│   ├── iam.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── .terraform.lock.hcl
│
├── .gitignore
└── README.md

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

ubuntu-latest
      │
      ▼
checkout repository
      │
      ▼
install Node 22
      │
      ▼
cd app
      │
      ▼
npm ci
      │
      ▼
install Chromium
      │
      ▼
npm test
      │
      ▼
1 passed ✅
