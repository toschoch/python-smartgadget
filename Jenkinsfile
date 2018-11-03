pipeline {
  agent {
    docker {
      image 'python:3-alpine'
    }

  }
  stages {
    stage('Test') {
      steps {
        echo 'Testing...'
        sh 'pip install -r requirements.txt'
        sh 'python setup.py test'
      }
    }
    stage('Build') {
      steps {
        echo 'Building...'
        sh 'python setup.py bdist_wheel'
        sh 'python setup.py sdist --formats=zip'

      }
    }
  }
  post {
    success {
        archiveArtifacts artifacts: 'dist/*.zip'
        archiveArtifacts artifacts: 'dist/*.whl'
    }
  }
}