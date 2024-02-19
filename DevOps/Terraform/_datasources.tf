locals {

  # General Settings
  project_tag_value = "ci-cd"

  # Codebuild Settings
  timeout                     = 60
  compute_type                = "BUILD_GENERAL1_SMALL"
  build_image                 = "aws/codebuild/amazonlinux2-aarch64-standard:3.0"
  type                        = "ARM_CONTAINER"
  taint_task_def              = false
  recreate_source_db_snapshot = false
  auto_approve                = false
  auto_shutdown               = true
  repository                  = "https://github.com/streamlyne-inc/ekualiti-devops.git"
  terraform_version           = "1.5.6"
  buildspec                   = "terraform/projects/ci_cd/buildspec/buildspec.yml"
  build_projects              = jsondecode(file("files/projects.json"))


  # Nexus Settings
  nexus_username = "cicd-user"
  nexus_password = "BnfKPuT8kMp6"

  # IAM Settings
  user_cicd_key_name = "cicd-user"
  user_cicd_trust_account_roles = [
    "arn:aws:iam::608692395687:role/terraform", # Sandbox
    "arn:aws:iam::000927316516:role/terraform", # Master
    "arn:aws:iam::632114636116:role/terraform", # Dev
    "arn:aws:iam::498648514905:role/terraform", # Alliant
    "arn:aws:iam::976108952504:role/terraform", # Amherst
    "arn:aws:iam::880916866199:role/terraform", # BVARI
    "arn:aws:iam::633131813382:role/terraform", # CVRE
    "arn:aws:iam::805920254122:role/terraform", # FGCU
    "arn:aws:iam::317093373915:role/terraform", # IASTATE
    "arn:aws:iam::840428843418:role/terraform", # KU
    "arn:aws:iam::119891150434:role/terraform", # MHRI
    "arn:aws:iam::695496790626:role/terraform", # NJIT
    "arn:aws:iam::328029167857:role/terraform", # NMSU
    "arn:aws:iam::864980315255:role/terraform", # PAVIR
    "arn:aws:iam::521465192007:role/terraform", # PONCE
    "arn:aws:iam::769287927215:role/terraform", # SCRIPPS
    "arn:aws:iam::502624185716:role/terraform", # TNTECH
    "arn:aws:iam::129408769352:role/terraform", # UASYS
    "arn:aws:iam::245147533264:role/terraform", # UCSC
    "arn:aws:iam::989129716982:role/terraform", # UNM
    "arn:aws:iam::747947880980:role/terraform", # UNCO
    "arn:aws:iam::888625601412:role/terraform", # UPR-CCC
    "arn:aws:iam::608248562560:role/terraform", # UPR-MAY
    "arn:aws:iam::725962033514:role/terraform", # UPR-RP
    "arn:aws:iam::445053420666:role/terraform", # UPR-MED
    "arn:aws:iam::450753166634:role/terraform", # VAI
    "arn:aws:iam::417812125612:role/terraform", # WHOI
  ]
}