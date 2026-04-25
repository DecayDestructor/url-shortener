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
                sh '''
                echo "Installing Python dependencies..."
                pip3 install --break-system-packages -r requirements.txt || pip3 install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // Run tests with verbose output
                sh '''
                echo "Running unit tests..."
                pytest -v
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                // Builds the frontend and backend images defined in docker-compose.yml
                sh '''
                echo "Building all Docker images (Frontend & Backend)..."
                
                # Build everything defined in docker-compose.yml
                docker compose build
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
