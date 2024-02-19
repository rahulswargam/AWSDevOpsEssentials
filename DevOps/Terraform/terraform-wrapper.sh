#!/bin/bash -e

TERRAFORM_COMMAND='terraform'

# Don't run if env, instance, and Terraform action are not given
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 TERRAFORM_ACTION [TERRAFORM_ARGUMENTS]"
    exit 1
fi

if ! command -v "${TERRAFORM_COMMAND}" > /dev/null; then
	echo "ERROR: '${TERRAFORM_COMMAND}' is not found on PATH; Aborting script!"
	exit 1
fi

# Get all arguments passed to this script and assign them to the correct variables
ENVIRONMENT="dev"
TERRAFORM_ACTION=$1
TERRAFORM_ARGUMENTS=( "${@:2}" )

# Delete empty values in TERRAFORM_ARGUMENTS
for i in "${!TERRAFORM_ARGUMENTS[@]}"; do
  [ -n "${TERRAFORM_ARGUMENTS[$i]}" ] || unset "TERRAFORM_ARGUMENTS[$i]"
done

ENVIRONMENTS_FOLDER="../../environments"

# Parse variable file and folder names
CLIENT_VAR_FILENAME="_environment.tfvars"
CLIENT_VAR_FILE="${ENVIRONMENTS_FOLDER}/${ENVIRONMENT}/${CLIENT_VAR_FILENAME}"

# Make sure all needed variable files exist
if [[ ! -f ${CLIENT_VAR_FILE} ]]; then
	echo "Can not find client variable file for ${ENVIRONMENT} environment! Please create a ${ENVIRONMENT}/${CLIENT_VAR_FILENAME} file in the 'environments' folder and run this script again."
	exit 1
fi

# Run init to set up the remote backend and download plugins
if [[ $TERRAFORM_ACTION == "init" ]]; then
	"${TERRAFORM_COMMAND}" "${TERRAFORM_ACTION}" "${TERRAFORM_ARGUMENTS[@]}"
else
	"${TERRAFORM_COMMAND}" init
fi

echo ""

# Change to the proper workspace for the instance
WORKSPACE="ci-cd"
if [[ $("${TERRAFORM_COMMAND}" workspace show) != "${WORKSPACE}" ]]; then
	if "${TERRAFORM_COMMAND}" workspace list | grep -E --quiet "${WORKSPACE}$"; then
		"${TERRAFORM_COMMAND}" workspace select "${WORKSPACE}"
	else
		echo "Can not find ${WORKSPACE} in Terraform workspaces. Creating workspace..."
		"${TERRAFORM_COMMAND}" workspace new "${WORKSPACE}"
	fi
	echo ""
fi

echo ""

if [[ $TERRAFORM_ACTION == "init" ]]; then
	echo "Requested Terraform action was 'init', so exiting now."
	exit 0
elif [[ $TERRAFORM_ACTION == "state" ]]; then
	LOCAL_STATE_FILE="${WORKSPACE}.tfstate"

	if [[ ${TERRAFORM_ARGUMENTS[0]} == "push" ]]; then
		if [[ -f ${LOCAL_STATE_FILE} ]]; then
			echo "Uploding state file ${LOCAL_STATE_FILE} to remote storage"
			"${TERRAFORM_COMMAND}" state push "${LOCAL_STATE_FILE}"
		else
			echo "Could not find local state file ${LOCAL_STATE_FILE}..."
		fi
	elif [[ ${TERRAFORM_ARGUMENTS[0]} == "pull" ]]; then
		echo "Writing state file to ${LOCAL_STATE_FILE}"
		"${TERRAFORM_COMMAND}" state pull > "${LOCAL_STATE_FILE}"
	else
		"${TERRAFORM_COMMAND}" "${TERRAFORM_ACTION}" "${TERRAFORM_ARGUMENTS[@]}"
	fi
	exit 0
fi

if ! command -v aws > /dev/null; then
	echo "ERROR: 'aws' is not found on PATH; Aborting script!"
	exit 1
fi

if ! command -v jq > /dev/null; then
	echo "ERROR: 'jq' is not found on PATH; Aborting script!"
	exit 1
fi

ASSUME_ROLE_NAME="terraform"
ASSUME_ROLE_DURATION="3600"
AWS_ACCOUNT_NUMBER=$(grep aws_account_number "${CLIENT_VAR_FILE}" | cut -d= -f2 | tr -d ' "')

ASSUME_ROLE_CREDS=$(aws --region 'us-east-1' --output json sts assume-role --role-arn "arn:aws:iam::${AWS_ACCOUNT_NUMBER}:role/${ASSUME_ROLE_NAME}" --role-session-name "${ENVIRONMENT}-ecs-terraform" --duration-seconds ${ASSUME_ROLE_DURATION})
ACCESS_KEY_ID=$(echo "${ASSUME_ROLE_CREDS}" | jq -r ".Credentials.AccessKeyId")
SECRET_ACCESS_KEY=$(echo "${ASSUME_ROLE_CREDS}" | jq -r ".Credentials.SecretAccessKey")
SESSION_TOKEN=$(echo "${ASSUME_ROLE_CREDS}" | jq -r ".Credentials.SessionToken")

# Apply the variable files in the proper order, if needed for the specified Terraform action
if [[ $TERRAFORM_ACTION == "import" || $TERRAFORM_ACTION == "plan" || $TERRAFORM_ACTION == "refresh" || $TERRAFORM_ACTION == "destroy" || ($TERRAFORM_ACTION == "apply" && "${TERRAFORM_ARGUMENTS[*]}" != *"plan"*) ]]; then
	TF_VARS_ARG=(
		"-var-file=${CLIENT_VAR_FILE}" \
		"-var=aws_access_key=${ACCESS_KEY_ID}" \
		"-var=aws_secret_key=${SECRET_ACCESS_KEY}" \
		"-var=aws_session_token=${SESSION_TOKEN}"
	)
fi

# Run the specified Terraform action
"${TERRAFORM_COMMAND}" "${TERRAFORM_ACTION}" "${TF_VARS_ARG[@]}" "${TERRAFORM_ARGUMENTS[@]}"

exit $?
