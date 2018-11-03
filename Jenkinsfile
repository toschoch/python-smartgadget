pipeline {
  agent {
    docker {
      image 'alpine:3.8'
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