# MY ROUGHT NOTES ON MAKING THIS WORK
###https://aws.amazon.com/blogs/security/how-to-build-a-multi-region-aws-security-hub-analytic-pipeline/

## IF PIP PLAYS UP
# pip install pip --upgrade
# pip install pyopenssl --upgrade


## sudo apt install nodejs npm -y
## sudo apt upgrade
## sudo apt update
## curl https://raw.githubusercontent.com/creationix/nvm/master/install.sh | bash
## nvm ls-remote
## # node 18.14.1 # was used for cdk for security lake, version 19.6.1 was used for this code
## nvm install 19.6.1
## npm install -g aws-cdk   


# cdk --version
# python3 -m venv .venv
source .venv/bin/activate
# pip install -r requirements.txt
# cdk bootstrap

## set creds before running!!
## export AWS_ACCESS_KEY_ID=""
## export AWS_SECRET_ACCESS_KEY=""
## export AWS_SESSION_TOKEN=""
## cdk deploy --all

## first run!
cdk deploy AnalyticSink Aggregation AthenaSecurityHub*