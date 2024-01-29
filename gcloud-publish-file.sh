set -eu

# This script is responsible for the following:
# 1. Upload a file $ARTIFACT to a $GS_URL
# 2. Creates a service account key from $GCLOUD_SA
# 3. Creates a signed URL for the updoaded file with the SA key created
#    from the previous step
#
# The script expects that the user has
# 1. logged in to the gcloud CLI
# 2. selected in gcloud the project they want to use
# 3. created a service account key, for pushing to bucket
#
# Some helper commands for the above are the following:
#
# gcloud auth login --no-launch-browser
# gcloud projects list
# gcloud config set project PROJECT_ID
# gcloud iam service-accounts keys create \
#     --iam-account=ckf-artifacts-storage-sa@thermal-creek-391110.iam.gserviceaccount.com
#     signing-sa-key.json \
#
# For more information you can take a look on the following links
# https://cloud.google.com/iam/docs/keys-create-delete#iam-service-account-keys-create-gcloud
# https://cloud.google.com/storage/docs/access-control/signing-urls-with-helpers

echo $FILE
echo $GS_URL
echo $GCLOUD_SA_KEY

FILE_URL=$GS_URL/$(basename $FILE)

echo "Copying \"$FILE\" to \"$GS_URL\""
gcloud storage cp -r $FILE $FILE_URL
echo "Successfully uploaded!"

echo "Creating signed url"
gcloud storage sign-url \
    --private-key-file=$GCLOUD_SA_KEY \
    --duration=7d \
    $FILE_URL
