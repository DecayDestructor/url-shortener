pipeline {
    agent any

    environment {
        SONAR_HOST_URL = "http://54.91.164.129:9000"
        SONAR_LOGIN    = "admin"
        SONAR_PASSWORD = "aaryan"
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
                # Copy the real server .env (with proper DB URL) before deploying
                cp /opt/URL-shortener/.env "${PWD}/.env"
                docker run --rm \
                  -v /var/run/docker.sock:/var/run/docker.sock \
                  -v url-shortener_jenkins_home:/var/jenkins_home \
                  -w "${PWD}" \
                  docker:cli \
                  docker compose -p url-shortener -f docker-compose.yml up -d --build backend frontend
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
