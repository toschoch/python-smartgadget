pipeline {
  agent {
    docker {
      image 'python:3-alpine'
      args '"/bin/ash"'
    }

  }
  stages {
    stage('Test') {
      steps {
        echo 'Testing...'
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