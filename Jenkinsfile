pipeline {
    agent any

    environment {
        // Tag for the built images
        IMAGE_TAG = "${env.BUILD_ID}"
    }

    stages {
        stage('Checkout') {
            steps {
                // Checks out the code from the configured Git repository
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                // Keeping it simple, no virtualenv.
                // Note: --break-system-packages is used for newer Debian versions 
                // in the Jenkins LTS image to allow system-wide pip installs.
                // --ignore-installed prevents pip from trying to uninstall apt-managed packages (like pytest)
                sh '''
                echo "Installing Python dependencies..."
                pip3 install --break-system-packages --ignore-installed -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // Run tests with verbose output
                // Create a dummy .env file configured for SQLite so FastAPI lifespan events don't fail trying to connect to a fake Postgres host
                sh '''
                echo "Creating dummy .env for tests..."
                echo "DATABASE_URL=sqlite://" > .env
                echo "REDIS_URL=redis://localhost:6379" >> .env
                echo "BASE_URL=http://localhost:8000" >> .env
                echo "JWT_SECRET_KEY=test-secret" >> .env
                echo "Running unit tests..."
                pytest -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                // Builds the frontend and backend images
                sh '''
                echo "Building all Docker images (Frontend & Backend)..."
                
                # Build Backend
                docker build -t url-shortener-backend:${IMAGE_TAG} -t url-shortener-backend:latest -f Dockerfile.backend .
                
                # Build Frontend
                docker build --build-arg VITE_API_URL=/api -t url-shortener-frontend:${IMAGE_TAG} -t url-shortener-frontend:latest -f Dockerfile.frontend .
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline complete. Cleaning up workspace..."
            cleanWs()
        }
        success {
            echo "Build & Test succeeded!"
        }
        failure {
            echo "Pipeline failed. Check logs for details."
        }
    }
}
