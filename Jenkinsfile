node('docker') {
    stage('Checkout') {
        checkout scm
        try { 
            env.VERSION = gitVersion()
            echo "Version = ${env.VERSION}"
            env.ISTAG = isTag()
            echo "Tag = ${env.ISTAG}"
        }
        catch(Exception e) {
            echo "could not read git version! Make sure that you do not make a shallow clone only..."
        }
    }

    // stage('UnitTest') {
    //     docker.image('python:3-alpine').inside {
    //         sh 'python setup.py test'
    //     }
    // }

    // stage('Build') {
    //     version = gitVersion()
    //     echo version
    //     version = '-e VERSION='+version
    //     docker.image('python:3-alpine').inside(version) {
    //         sh 'rm -rf ./dist'
    //         sh 'python setup.py bdist_wheel'
    //     }
    // }
    
    stage('Publish') {

        devpiUrl = "http://devpi.dietzi.mywire.org"

        index = "staging"
        if (isTag()) {
            index = "stable"
        }
        echo "deploy to '${devpiUrl}' to the '${index}' index..."

        docker
        .image('shocki/alpine-devpi-client')
        .inside("-u jenkins:root -e INDEX=${index} -e URL=${devpiUrl}") {
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

def getCommit() {
    return sh(script: 'git rev-parse HEAD', returnStdout: true)?.trim()
}

def gitDescription() {
    return sh(script: "git describe --tags --long --dirty", returnStdout: true)?.trim()
}

def gitVersion() {
    desc = gitDescription()
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
    desc = gitDescription()
    parts = desc.split('-')
    assert parts.size() in [3, 4]
    dirty = (parts.size() == 4)
    tag = parts[0]
    count = parts[1]
    sha = parts[2]
    return (count == '0' && !dirty)
}