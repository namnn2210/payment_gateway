pipeline {
    agent any

    environment {
        SSH_CREDENTIALS_ID = 'payment-gateway'  // The ID of your Jenkins Username/Password credentials
        REMOTE_SERVER = '15.235.131.24'         // The server IP or hostname
        SSH_PORT = '22'                         // The SSH port
        PROJECT_DIR = '/root/python/payment_gateway'  // The project directory on the remote server
    }

    stages {
        stage('Update Project and Restart Supervisor') {
            steps {
                // Use the withCredentials block to securely handle username and password
                withCredentials([usernamePassword(credentialsId: SSH_CREDENTIALS_ID, usernameVariable: 'SSH_USER', passwordVariable: 'SSH_PASS')]) {
                    sh """
                        sshpass -p $SSH_PASS ssh -o StrictHostKeyChecking=no -p ${SSH_PORT} ${SSH_USER}@${REMOTE_SERVER} '
                            cd ${PROJECT_DIR} &&
                            git pull &&
                            supervisorctl restart fetch_acb_info fetch_mb_info fetch_mb_corp_info fetch_tech_info fetch_vietin_info payment payout_submit
                        '
                    """
                }
            }
        }
    }
}
