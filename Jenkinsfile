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
        sh 'echo "Hello World"'
      }
    }
    stage('Build') {
      steps {
        echo 'Building...'
        sh 'echo "Hello World"'
        sh 'ls -la'
      }
    }
  }
}