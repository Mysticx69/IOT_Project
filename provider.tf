provider "aws" {
  region = "us-east-1"
}

terraform {
  required_version = "~>1.3.3"

  required_providers {
    aws      = "~>4"
    template = "~>2.2"
  }
}
