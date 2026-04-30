pipeline {
    agent any

    environment {
        SONAR_HOST_URL = "http://54.91.164.129:9000"
        SONAR_LOGIN    = "admin"
        SONAR_PASSWORD = "admin123"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                echo "Running tests inside Python Docker container..."
                docker run --rm -v url-shortener_jenkins_home:/var/jenkins_home -w "${PWD}" python:3.12-slim bash -c "
                    pip install --no-cache-dir -r requirements.txt &&
                    echo 'DATABASE_URL=sqlite://' > .env &&
                    echo 'REDIS_URL=redis://localhost:6379' >> .env &&
                    echo 'BASE_URL=http://localhost:8000' >> .env &&
                    echo 'JWT_SECRET_KEY=test-secret' >> .env &&
                    pytest -v
                "
                '''
            }
        }

        stage('SonarQube Analysis') {
            steps {
                sh '''
                echo "Running SonarQube Scanner..."
                docker run --rm --network host \
                  -v url-shortener_jenkins_home:/var/jenkins_home \
                  -w "${PWD}" \
                  sonarsource/sonar-scanner-cli \
                  -Dsonar.host.url="${SONAR_HOST_URL}" \
                  -Dsonar.login="${SONAR_LOGIN}" \
                  -Dsonar.password="${SONAR_PASSWORD}" \
                  -Dsonar.projectKey=url-shortener \
                  -Dsonar.projectName="Snip.ly URL Shortener" \
                  -Dsonar.sources=.
                '''
            }
        }

        stage('Deploy to Server') {
            steps {
                sh '''
                echo "Rebuilding and Deploying containers live..."
                # Since Jenkins is on the same server, we can just trigger Docker Compose!
                docker compose -f docker-compose.cloud.yml build backend frontend
                docker compose -f docker-compose.cloud.yml up -d backend frontend
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Cleaning workspace..."
            cleanWs()
        }
        success {
            echo "SUCCESS: App successfully analyzed and deployed!"
        }
        failure {
            echo "FAILURE: Check console output for details."
        }
    }
}
