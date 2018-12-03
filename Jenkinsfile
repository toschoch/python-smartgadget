
def getCommit() {
    return sh(script: 'git rev-parse HEAD', returnStdout: true)?.trim()
}

def gitVersion() {
    commit = getCommit()
    if (commit) {
        sh(script: "git fetch --unshallow")
        desc = sh(script: "git describe --tags --long --dirty ${commit}", returnStdout: true)?.trim()
        parts = desc.split('-')
        assert len(parts) in [3, 4]
        dirty = len(parts) == 4
        tag = parts[0]
        count = parts[1]
        sha = parts[2]
        if (count == '0' && !dirty) {
            return tag
        }
        return sprintf( '%1$s.dev%2$s+%3$s', [tag, count, sha.substring(1)])
    }
    return null
}

def isTag() {
    commit = getCommit()
    if (commit) {
        sh(script: "git fetch --unshallow")
        desc = sh(script: "git describe --tags --long --dirty ${commit}", returnStdout: true)?.trim()
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
