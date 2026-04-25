pipeline {
    agent any

    environment {
        // ── Docker Hub username and existing repo names ──
        DOCKERHUB_USER  = "vriva"
        BACKEND_IMAGE   = "${DOCKERHUB_USER}/url-shortener-backend"
        FRONTEND_IMAGE  = "${DOCKERHUB_USER}/url-shortener-frontend"
        IMAGE_TAG       = "${env.BUILD_ID}"

        // ── EC2 server details ──
        EC2_HOST        = "3.81.31.34"
        EC2_USER        = "ubuntu"
    }

    stages {

        // ─────────────────────────────────────────────
        // STAGE 1: Pull latest code from GitHub
        // ─────────────────────────────────────────────
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 2: Install Python deps for testing
        // ─────────────────────────────────────────────
        stage('Install Dependencies') {
            steps {
                sh '''
                echo "Installing Python dependencies..."
                pip3 install --break-system-packages --ignore-installed -r requirements.txt
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 3: Run all 85 pytest tests (mocked DB & Redis)
        // ─────────────────────────────────────────────
        stage('Run Tests') {
            steps {
                sh '''
                echo "Creating test .env..."
                echo "DATABASE_URL=sqlite://"            > .env
                echo "REDIS_URL=redis://localhost:6379"  >> .env
                echo "BASE_URL=http://localhost:8000"    >> .env
                echo "JWT_SECRET_KEY=test-secret"        >> .env
                echo "Running tests..."
                pytest -v
                '''
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 4: Build Docker images & push to Docker Hub
        // Credential ID: 'dockerhub-creds' (set up in Jenkins)
        // ─────────────────────────────────────────────
        stage('Build & Push Docker Images') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh '''
                    echo "Logging in to Docker Hub..."
                    echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin

                    echo "Building Backend image..."
                    docker build \
                        -t ${BACKEND_IMAGE}:${IMAGE_TAG} \
                        -t ${BACKEND_IMAGE}:latest \
                        -f Dockerfile.backend .

                    echo "Building Frontend image..."
                    docker build \
                        --build-arg VITE_API_URL=/api \
                        -t ${FRONTEND_IMAGE}:${IMAGE_TAG} \
                        -t ${FRONTEND_IMAGE}:latest \
                        -f Dockerfile.frontend .

                    echo "Pushing images to Docker Hub..."
                    docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                    docker push ${BACKEND_IMAGE}:latest
                    docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                    docker push ${FRONTEND_IMAGE}:latest

                    docker logout
                    echo "Push complete!"
                    '''
                }
            }
        }

        // ─────────────────────────────────────────────
        // STAGE 5: SSH into AWS EC2 and redeploy live app
        // Credential ID: 'ec2-ssh-key' (set up in Jenkins)
        // ─────────────────────────────────────────────
        stage('Deploy to EC2') {
            steps {
                withCredentials([sshUserPrivateKey(
                    credentialsId: 'ec2-ssh-key',
                    keyFileVariable: 'SSH_KEY'
                )]) {
                    sh '''
                    echo "Deploying to EC2 at ${EC2_HOST}..."
                    ssh -o StrictHostKeyChecking=no -i "$SSH_KEY" ${EC2_USER}@${EC2_HOST} "
                        docker-compose -f ~/docker-compose.prod.yml pull &&
                        docker-compose -f ~/docker-compose.prod.yml down &&
                        docker-compose -f ~/docker-compose.prod.yml up -d --remove-orphans
                    "
                    echo "Deployment complete! App is live at http://${EC2_HOST}"
                    '''
                }
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Cleaning workspace..."
            cleanWs()
        }
        success {
            echo "SUCCESS: App deployed to http://${EC2_HOST}"
        }
        failure {
            echo "FAILURE: Check console output for details."
        }
    }
}
