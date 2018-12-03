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
        def shorthash = sh(returnStdout: true, script: "git rev-parse --short HEAD").trim()
        def version = '-e VERSION='+shorthash
        echo version
        docker.image('python:3-alpine').inside(version) {
            sh 'python setup.py bdist_wheel'
        }
    }
    stage('Publish') {
        docker.build('upload','./dockerfiles/upload').inside('-u root:root') { c ->
            withCredentials([usernamePassword(credentialsId: 'dietzi devpi', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                sh 'devpi use http://devpi.dietzi.mywire.org/${USERNAME}/staging'
                sh 'devpi login --password ${PASSWORD} ${USERNAME}'
            }
            sh 'devpi upload dist/*.whl'
        }
    }
}
