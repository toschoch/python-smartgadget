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
            sh 'ls -la /usr/bin'

        }
    }
}