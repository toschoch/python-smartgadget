node('docker') {
    stage('Checkout') {
        checkout scm
    }
    stage('UnitTest') {
        docker.image('python:3-alpine').inside {
            sh 'python setup.py test'
        }
    }
    stage('Build') {
        docker.image('python:3-alpine').inside {
            env.VERSION=env.GIT_COMMIT
            sh 'python setup.py bdist_wheel'
        }
    }
    stage('Publish') {
        docker.build('upload','./dockerfiles/upload').withRun('-u root:root') {
            sh 'pip install devpi-client'
            withCredentials([usernamePassword(credentialsId: 'dietzi devpi', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                sh 'devpi use http://devpi.dietzi.mywire.org/${USERNAME}/staging'
                sh 'devpi login --password ${PASSWORD} ${USERNAME}'
            }
            sh 'devpi upload dist/*.whl'

        }
    }
}