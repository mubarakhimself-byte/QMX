<!-- Source: https://openobserve.ai/downloads/
     Fetched: 2026-10-28. Text extracted from the HTML page (markup, scripts and navigation removed). -->

Download OpenObserve | Free Cloud or Self-Hosted Setup 

Skip to main content

 Upcoming Webinar: 
Getting Started with OpenObserve

 November 05, 2026
 11:00 AM ETRegister 

- 
- 
- 
- 
- 

# Downloads

## Try OpenObserve Cloud
Fully managed. Get started in minutes.

- No infrastructure to manage
- Automatic updates
- 24/7 support
Start Free Trial

## Configure Your Download

Version
 Latest (v1.1.2) v1.1.1v1.1.0v1.0.4v1.0.3v1.0.2v1.0.1v1.0.0v0.92.2v0.92.1v0.92.0v0.91.5v0.91.4v0.91.3v0.91.2v0.91.1v0.91.0v0.90.3v0.90.2v0.90.1

Edition
EnterpriseOpen Source (OSS)

Deployment Mode
Single NodeHigh Availability (HA)

### High Availability Deployment
For HA deployments, please refer to our detailed documentation for setup instructions and best practices. View HA Deployment Guide 

 This version may include bugs or unstable features. Downloading a stable release is recommended. 

Enterprise
 Released: Oct 20, 2026Oct 16, 2026Oct 14, 2026Sep 24, 2026Sep 18, 2026Sep 17, 2026Sep 16, 2026Sep 11, 2026Aug 17, 2026Aug 14, 2026Aug 07, 2026Jul 29, 2026Jul 28, 2026Jul 21, 2026Jul 17, 2026Jul 02, 2026Jun 22, 2026May 26, 2026May 22, 2026May 21, 2026 View Changelog 

- •Much Higher Performance
- •SSO with Custom Auth Providers (Okta, Microsoft Entra, etc)
- •Role-based Access Control (RBAC)
Learn more about Enterprise

Linux

macOS

Windows

Docker

Kubernetes

### Linux (64 Bit)

Quick downloadManual download

curl -L https://raw.githubusercontent.com/openobserve/openobserve/main/downloadO2.sh | sh -s o2-enterprise v1.1.2

#### Manual Download with curl

#For arm64
curl -L -o openobserve-ee-v1.1.2-linux-arm64.tar.gz https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-linux-arm64.tar.gz && tar -xzf openobserve-ee-v1.1.2-linux-arm64.tar.gz

 Show SHA256 

#For amd64
curl -L -o openobserve-ee-v1.1.2-linux-amd64.tar.gz https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-linux-amd64.tar.gz && tar -xzf openobserve-ee-v1.1.2-linux-amd64.tar.gz

 Show SHA256 

#For amd64-simd
curl -L -o openobserve-ee-v1.1.2-linux-amd64-simd.tar.gz https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-linux-amd64-simd.tar.gz && tar -xzf openobserve-ee-v1.1.2-linux-amd64-simd.tar.gz

 Show SHA256 

#For amd64-musl
curl -L -o openobserve-ee-v1.1.2-linux-amd64-musl.tar.gz https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-linux-amd64-musl.tar.gz && tar -xzf openobserve-ee-v1.1.2-linux-amd64-musl.tar.gz

 Show SHA256 

#### Run OpenObserve

export ZO_ROOT_USER_EMAIL=root@example.com
export ZO_ROOT_USER_PASSWORD=Complexpass#123
 ./openobserve

Now point your browser to http://localhost:5080 and login

Getting glibc error running binary?
./openobserve: `/lib/libm.so.6`: version `GLIBC_2.27` not found (required by ./openobserve)
Download the musl binary instead of regular binary from releases page that has no external dependencies. This binary is not as performant as other binaries though. We recommend running the containerized version if performance is a concern for you and are unable to make the dependencies work.

### Windows (64 Bit)

#### PowerShell Download

Invoke-WebRequest -Uri "https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-windows-amd64.zip" -OutFile "openobserve-ee-v1.1.2-windows-amd64.zip"

 Show SHA256 

Expand-Archive -Path "openobserve-ee-v1.1.2-windows-amd64.zip" -DestinationPath .

#### Run OpenObserve

#command prompt
set ZO_ROOT_USER_EMAIL=root@example.com
set ZO_ROOT_USER_PASSWORD=Complexpass#123
openobserve.exe

#powershell
$env:ZO_ROOT_USER_EMAIL="root@example.com"
$env:ZO_ROOT_USER_PASSWORD="Complexpass#123"
openobserve.exe

Now point your browser to http://localhost:5080 and login

### macOS (Intel and Apple Silicon)

Quick downloadManual download

curl -L https://raw.githubusercontent.com/openobserve/openobserve/main/downloadO2.sh | sh -s o2-enterprise v1.1.2

#### Intel Macs
No manual download available for the Enterprise version.

#### Apple Silicon

curl -L -o openobserve-ee-v1.1.2-darwin-arm64.tar.gz https://downloads.openobserve.ai/releases/o2-enterprise/v1.1.2/openobserve-ee-v1.1.2-darwin-arm64.tar.gz && tar -zxvf openobserve-ee-v1.1.2-darwin-arm64.tar.gz

 Show SHA256 

#### Run OpenObserve

export ZO_ROOT_USER_EMAIL=root@example.com
export ZO_ROOT_USER_PASSWORD=Complexpass#123
 ./openobserve

Now point your browser to http://localhost:5080 and login

### Docker
Docker images are available at https://gallery.ecr.aws/zinclabs/openobserve-enterprise

#### Docker Run

docker run -v $PWD/data:/data -e ZO_DATA_DIR="/data" -p 5080:5080 \
 -e ZO_ROOT_USER_EMAIL="root@example.com" -e ZO_ROOT_USER_PASSWORD="Complexpass#123"
 o2cr.ai/openobserve/openobserve-enterprise:v1.1.2

Now point your browser to http://localhost:5080 and login

Error pulling image if you have AWS CLI installed?
If you have AWS CLI installed and get login error then run below command:
aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin public.ecr.aws

### Kubernetes - Manifest

#### Create namespace:

kubectl create namespace openobserve

#### Create a deployment.yaml file

apiVersion: v1
kind: Service
metadata:
 name: openobserve
 namespace: openobserve
spec:
 clusterIP: None
 selector:
 app: openobserve
 ports:
 - name: http
 port: 5080
 targetPort: 5080
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
 name: openobserve
 namespace: openobserve
 labels:
 name: openobserve
spec:
 serviceName: openobserve
 replicas: 1
 selector:
 matchLabels:
 name: openobserve
 app: openobserve
 template:
 metadata:
 labels:
 name: openobserve
 app: openobserve
 spec:
 securityContext:
 fsGroup: 2000
 runAsUser: 10000
 runAsGroup: 3000
 runAsNonRoot: true
 containers:
 - name: openobserve
 image: o2cr.ai/openobserve/openobserve-enterprise:latest
 env:
 - name: ZO_ROOT_USER_EMAIL
 value: root@example.com
 - name: ZO_ROOT_USER_PASSWORD
 value: Complexpass#123
 - name: ZO_DATA_DIR
 value: /data
 imagePullPolicy: Always
 resources:
 limits:
 cpu: 4096m
 memory: 2048Mi
 requests:
 cpu: 256m
 memory: 50Mi
 ports:
 - containerPort: 5080
 name: http
 volumeMounts:
 - name: data
 mountPath: /data
 volumeClaimTemplates:
 - metadata:
 name: data
 spec:
 accessModes:
 - ReadWriteOnce
 resources:
 requests:
 storage: 10Gi

#### Access the service

kubectl -n openobserve port-forward svc/openobserve 5080:5080

Now point your browser to http://localhost:5080 and login

## Open Source vs Enterprise Edition Comparison

### Why Choose Open Source?

Best suited for individual developers and home lab use cases.

### Why Choose Enterprise?

Free up to 50 GB/day ingestion
Best suited for all business use cases, Enterprise provides additional performance features, user management, and security capabilities.

Open Source vs Enterprise Edition Comparison
 | Category | Open Source | Enterprise Edition 
 | Licenses & Cost
 | License Type | 
AGPL-3.0 | 
End User License Agreement
 | Cost | 
Free without limits | 
*Free up to 50 GB/day ingestion
 | Core Capabilities
 | Metrics | 
Full support | 
Full support
 | Logs | 
Full support | 
Full support
 | Traces | 
Full support | 
Full support
 | Real User Monitoring (RUM) | 
Full support | 
Full support
 | Data Pipelines | 
Available, limited functionality | 
Full support including remote destinations
 | Dashboards | 
Full support, 19 prebuilt chart types + custom | 
Full support, 19 prebuilt chart types + custom
 | Alerts | 
Full support | 
Full support
 | Federated Search / Super Cluster | 
Not available | 
Full support
 | Query Management | 
Not available | 
Full support
 | Workload Management (QoS) | 
Not available | 
Full support
 | Quotas & Rate Limiting | 
Basic | 
Full support
 | Security Capabilities
 | TLS Encryption | 
TLS 1.2+ | 
TLS 1.2+
 | Storage Encryption | 
Via cloud provider KMS | 
Via cloud provider KMS
 | Basic Authentication | 
Email + password | 
Email + password
 | Single Sign-On (SSO) | 
Not available | 
OIDC, SAML 2.0, Okta, Azure Entra, LDAP/AD, GitHub, GitLab, Google, Keycloak + more (Requires HA Mode)
 | HIPAA Compliance Support | 
Self-managed | 
Yes (requires addendum)
 | PCI-DSS Compliance Support | 
Self-managed | 
Yes (requires addendum)
 | Audit Trail | 
Basic logging only | 
Comprehensive 365-day immutable logs
 | User Management & Authentication
 | Root User Account | 
Created at startup | 
Created at startup
 | Multiple Users | 
Yes, including system roles: Admin, Editor, User, and Viewer | 
With role-based permissions
 | Role-Based Access Control (RBAC) | 
All users have full access | 
Admin, Editor, Viewer, User, Root, Custom roles (Requires HA Mode)
 | Custom Roles | 
Not available | 
Granular permission management
 | User Groups | 
Not available | 
Collective permission management
 | Service Accounts | 
Full access only | 
Role-based token authentication
 | Multi-Tenancy | 
Organizations and streams | 
Organizations and streams with quotas
 | Data Retention & Storage
 | Default Retention | 
User-configurable | 
User-configurable
 | Storage Format | 
Parquet | 
Parquet
 | Metadata Storage | 
SQLite (single node), PostgreSQL (HA) | 
SQLite (single node), PostgreSQL (HA)
 | Backup & Recovery | 
Customer-managed | 
Customer-managed
 | Support & SLAs
 | Support Type | 
Community | 
Priority w/ contract
 | Response Time Guarantees | 
Best-effort | 
Yes, w/ contract
 | SLA Guarantees | 
None | 
Yes, w/ contract
 | Support Channels | 
Slack community | 
Dedicated
 | Update Requirements | 
Self-managed | 
Faster critical security updates

## Additional Resources

### Documentation
Complete guides and API references
View Docs →

### Cloud Trial
Try OpenObserve Cloud for free

Start Free Trial

### GitHub
Source code and community
Visit GitHub → 

### 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 
- 

### 
- 
- 
- 
- 
- 
- 

### 

We're live on Product Hunt

AI Observability by OpenObserve

OpenTelemetry-native observability for agents and LLMs.

Support us on Product Hunt
