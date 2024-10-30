pipeline {
    agent any

    environment {
        SSH_CREDENTIALS_ID = 'payment-gateway'  // The ID of your SSH credentials
        REMOTE_SERVER = '15.235.131.24'     // Replace with the actual username and server address
        SSH_PORT = '22'
        PROJECT_DIR = '/root/python/payment_gateway'
    }

    stages {
        stage('Update Project and Rebuild and Restart Supervisor') {
            steps {
                sshagent (credentials: [SSH_CREDENTIALS_ID]) {
                    sh """
                        ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${REMOTE_SERVER} '
                            cd ${PROJECT_DIR} &&
                            git pull origin main &&
                            supervisorctl restart all
                        '
                    """
                }
            }
        }
    }
}
