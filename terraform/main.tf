terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_security_group" "devops_sg" {
  name        = "devops-stack-sg"
  description = "Allow inbound traffic for Jenkins, SonarQube, App, and SSH"

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP (App)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Backend API"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Jenkins"
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SonarQube"
    from_port   = 9000
    to_port     = 9000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "tls_private_key" "devops_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "devops_key_pair" {
  key_name   = "devops-auto-key"
  public_key = tls_private_key.devops_key.public_key_openssh
}

resource "local_file" "private_key" {
  content         = tls_private_key.devops_key.private_key_pem
  filename        = "${path.module}/../devops-key.pem"
  file_permission = "0400"
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

resource "aws_instance" "devops_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.small"
  key_name      = aws_key_pair.devops_key_pair.key_name
  vpc_security_group_ids = [aws_security_group.devops_sg.id]

  root_block_device {
    volume_size = 20
  }

  tags = {
    Name = "DevOps-Stack-Server"
  }

  user_data = <<-EOF
              #!/bin/bash
              # --- Create 4GB Swap Space (CRITICAL for t2.micro to run Jenkins+SonarQube) ---
              fallocate -l 4G /swapfile
              chmod 600 /swapfile
              mkswap /swapfile
              swapon /swapfile
              echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
              # ------------------------------------------------------------------------------

              apt-get update
              apt-get install -y software-properties-common git
              add-apt-repository --yes --update ppa:ansible/ansible
              apt-get install -y ansible
              
              mkdir -p /opt/URL-shortener/ansible
              
              # Pull the latest code (even if without current local changes)
              git clone https://github.com/VriVa/URL-shortener.git /tmp/repo
              cp -r /tmp/repo/* /opt/URL-shortener/
              
              # Write docker-compose.cloud.yml
              cat << 'DOCKER' > /opt/URL-shortener/docker-compose.cloud.yml
              services:
                sonarqube:
                  image: sonarqube:10.4-community
                  container_name: sonarqube
                  ports:
                    - "9000:9000"
                  environment:
                    - SONAR_ES_BOOTSTRAP_CHECKS_DISABLE=true
                  restart: unless-stopped
                  networks:
                    - devops_network

                jenkins:
                  image: jenkins/jenkins:lts
                  container_name: jenkins
                  user: root
                  ports:
                    - "8080:8080"
                    - "50000:50000"
                  volumes:
                    - jenkins_home:/var/jenkins_home
                    - /var/run/docker.sock:/var/run/docker.sock
                    - /usr/bin/docker:/usr/bin/docker
                  restart: unless-stopped
                  networks:
                    - devops_network

                redis:
                  image: redis:7-alpine
                  container_name: snip_redis
                  restart: unless-stopped
                  ports:
                    - "6379:6379"
                  healthcheck:
                    test: ["CMD", "redis-cli", "ping"]
                    interval: 10s
                    timeout: 5s
                    retries: 5
                  networks:
                    - devops_network

                backend:
                  build:
                    context: .
                    dockerfile: Dockerfile.backend
                  container_name: snip_backend
                  restart: unless-stopped
                  ports:
                    - "8000:8000"
                  env_file:
                    - .env
                  environment:
                    REDIS_URL: redis://redis:6379
                    BASE_URL: http://localhost:8000
                  depends_on:
                    redis:
                      condition: service_healthy
                  networks:
                    - devops_network

                frontend:
                  build:
                    context: .
                    dockerfile: Dockerfile.frontend
                    args:
                      VITE_API_URL: /api
                  container_name: snip_frontend
                  restart: unless-stopped
                  ports:
                    - "80:80"
                  depends_on:
                    - backend
                  networks:
                    - devops_network

              volumes:
                jenkins_home:

              networks:
                devops_network:
                  name: devops_network
                  driver: bridge
              DOCKER

              # Write ansible playbook
              cat << 'PLAYBOOK' > /opt/URL-shortener/ansible/install_stack.yml
              - name: Install Docker and start DevOps Stack
                hosts: localhost
                connection: local
                become: yes
                tasks:
                  - name: Update apt packages
                    apt:
                      update_cache: yes

                  - name: Install required dependencies
                    apt:
                      name:
                        - apt-transport-https
                        - ca-certificates
                        - curl
                        - software-properties-common
                      state: present

                  - name: Add Docker GPG apt Key
                    apt_key:
                      url: https://download.docker.com/linux/ubuntu/gpg
                      state: present

                  - name: Add Docker Repository
                    apt_repository:
                      repo: deb https://download.docker.com/linux/ubuntu focal stable
                      state: present

                  - name: Install Docker
                    apt:
                      name:
                        - docker-ce
                        - docker-ce-cli
                        - containerd.io
                        - docker-compose-plugin
                      state: present

                  - name: Ensure Docker service is running
                    systemd:
                      name: docker
                      state: started
                      enabled: yes

                  - name: Create .env file for the application
                    copy:
                      dest: /opt/URL-shortener/.env
                      content: |
                        DATABASE_URL=sqlite:///./sql_app.db
                        REDIS_URL=redis://redis:6379
                        BASE_URL=http://localhost:8000
                        JWT_SECRET_KEY=devops-secret-key-12345

                  - name: Fix permissions for docker socket so Jenkins can use it
                    file:
                      path: /var/run/docker.sock
                      mode: '0666'
                    ignore_errors: yes

                  - name: Start the Docker Compose stack
                    command: docker compose -f docker-compose.cloud.yml up -d
                    args:
                      chdir: /opt/URL-shortener

                  - name: Wait a moment for jenkins
                    pause:
                      seconds: 5

                  - name: Set permissions for Jenkins home
                    command: docker exec -u root jenkins chown -R jenkins:jenkins /var/jenkins_home
                    ignore_errors: yes
              PLAYBOOK

              cd /opt/URL-shortener
              ansible-playbook ansible/install_stack.yml
              EOF
}

output "devops_server_public_ip" {
  value = aws_instance.devops_server.public_ip
}
