node('docker') {
    stage 'Checkout' {
        checkout scm
    }
    stage 'UnitTest' {
        docker.image('python:3-alpine') { c ->
            sh python setup.py test
        }
    }
    stage 'Build' {
        docker.image('python:3-alpine') { c ->
            sh python setup.py bdist_wheel
        }
    }
}