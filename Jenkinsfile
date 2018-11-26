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
            env.VERSION=env.BUILD_ID
            sh 'python setup.py bdist_wheel'
        }
    }
    stage('Publish') {
        docker.image('python:3-alpine').inside {
            sh 'pip install devpi-client'
            withCredentials([string(credentialsId: 'dietzi devpi', variable: 'USER'),
                             string(credentialsId: 'dietzi devpi', variable: 'PWD')]) {
                sh 'devpi use http://devpi.dietzi.mywire.org/${USER}/staging'
                sh 'devpi login --password ${PWD} ${USER}'
            }
            sh 'devpi upload /dist/*.whl'
        }
    }
}