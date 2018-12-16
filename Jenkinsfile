
def getCommit() {
    return sh(script: 'git rev-parse HEAD', returnStdout: true)?.trim()
}

def gitVersion() {
    desc = sh(script: "git describe --tags --long --dirty", returnStdout: true)?.trim()
    parts = desc.split('-')
    assert parts.size() in [3, 4]
    dirty = (parts.size() == 4)
    tag = parts[0]
    count = parts[1]
    sha = parts[2]
    if (count == '0' && !dirty) {
        return tag
    }
    return sprintf( '%1$s.dev%2$s+%3$s', [tag, count, sha.substring(1)])
}

def isTag() {
    commit = getCommit()
    if (commit) {
        desc = sh(script: "git describe --tags --long ${commit}", returnStdout: true)?.trim()
        match = desc =~ /.+-[0-9]+-g[0-9A-Fa-f]{6,}$/
        result = !match
        match = null
        return result
    }
    return false
}

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
        version = gitVersion()
        echo version
        version = '-e VERSION='+version
        docker.image('python:3-alpine').inside(version) {
            sh 'rm -rf ./dist'
            sh 'python setup.py bdist_wheel'
        }
    }
    stage('Publish') {

        devpiUrl = "http://devpi.dietzi.mywire.org"

        index = "staging"
        if (isTag()) {
            index = "stable"
        }
        echo "deploy to '${devpiUrl}' to the '${index}' index..."
        docker
        .image('shocki/alpine-devpi-client')
        .inside("--entrypoint /bin/ash -u root:root -e INDEX=${index} -e URL=${devpiUrl}") { c ->
            withCredentials([
                usernamePassword(credentialsId: 'dietzi devpi', 
                usernameVariable: 'USERNAME', 
                passwordVariable: 'PASSWORD')]) {
                sh 'devpi use ${URL}/${USERNAME}/${INDEX}'
                sh 'devpi login --password ${PASSWORD} ${USERNAME}'
            }
            sh 'devpi upload dist/*.whl'
        }
    }
}
