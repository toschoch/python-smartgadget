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
        def version = getGitVersion()
        echo version
        version = '-e VERSION='+version
        docker.image('python:3-alpine').inside(version) {
            sh 'rm -r ./dist'
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

String getGitVersion() {

    version = sh(script: "git describe --tags --long --dirty", returnStdout: true)?.trim()
    def parts = version.split('-')
    assert len(parts) in [3, 4]
    def dirty = len(parts) == 4
    def tag = parts[0]
    def count = parts[1]
    def sha = parts[2]
    if (count == '0' && !dirty) {
        return tag
    }
    return sprintf( '%1$s.dev%2$s+%3$s', [tag, count, sha.substring(1)])
}