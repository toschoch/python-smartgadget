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
        sh 'exit()'
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