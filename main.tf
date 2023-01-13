#################################################
#Call My Private VPC Module
#################################################
locals {
  region                       = "us-east-1"
  mockinfra_availability_zones = ["${local.region}a", "${local.region}b", "${local.region}c"]
}

module "vpc" {
  source = "git::https://github.com/Mysticx69/terraform-aws-vpc.git?ref=v1.0.2"

  # insert required variables here
  environment          = "IOT_PROJECT"
  vpc_cidr             = "10.150.0.0/16"
  public_subnets_cidr  = ["10.150.1.0/24", "10.150.2.0/24"]
  private_subnets_cidr = ["10.150.100.0/24", "10.150.200.0/24"]
  availability_zones   = local.mockinfra_availability_zones

  tags = {
    DeployedBy = "Terraform"
    Project    = "IOT-project"
  }
}

#################################################
#Create EC2 for API Rest
#################################################
resource "aws_instance" "iot" {
  ami             = "ami-06878d265978313ca"
  ebs_optimized   = true
  instance_type   = "t3.medium"
  key_name        = "vockey"
  subnet_id       = element(element(module.vpc.public_subnets_id, 1), 0)
  user_data       = file("./scripts/provisioning.sh")
  security_groups = [aws_security_group.iot_sg.id]

  tags = {
    "Name" = "IOT_PROJECT"
  }
}

#################################################
#Create EIP
#################################################
resource "aws_eip" "pip" {
  vpc      = true
  instance = aws_instance.iot.id
}

#################################################
#Create Security Group
#################################################
resource "aws_security_group" "iot_sg" {
  name        = "Allow-All"
  description = "Security group for webserver"
  vpc_id      = module.vpc.vpc_id

  tags = {
    "Name" = "AllowAll_SG"
  }
}

resource "aws_security_group_rule" "allowall_igress" {
  security_group_id = aws_security_group.iot_sg.id
  description       = "Allow all access to webserver inboud"
  type              = "ingress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_security_group_rule" "allowall_egress" {
  security_group_id = aws_security_group.iot_sg.id
  description       = "Allow all access to webserver egress"
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  cidr_blocks       = ["0.0.0.0/0"]
}





