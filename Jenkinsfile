pipeline {
  agent {
    docker {
      image 'python:3-alpine'
    }
  }
  environment {
    DIETZI_DEVPI = credentials('dietzi-devpi')
  }
  stages {
    stage('Test') {
      steps {
        echo 'Testing...'
        sh 'pip install -r requirements.txt'
        //sh 'python setup.py test'
      }
    }
    stage('Build') {
      steps {
        echo 'Building...'
        sh 'python setup.py bdist_wheel'
        sh 'python setup.py sdist --formats=zip'

      }
    }

    stage('Deploy') {
        steps {
            echo 'Deploying...'
            docker.image('mhoush/devpi-client').inside {
                sh 'devpi use http://dietzi.ddns.net:3141/dietzi/staging'
                sh 'devpi login ${DIETZI_DEVPI_USR} --password ${DIETZI_DEVPI_PSW}'
                sh 'devpi upload dietzi/*.zip'
                sh 'devpi upload dietzi/*.whl'
          }
        }
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