#!/usr/bin/bash
#
# This script parses given bundle file for github repositories and branches. Then checks out each
# charm's repository one by one using specified branch and collects images referred by that charm
# using that repository's image collection script
#
BUNDLE_FILE=$1
IMAGES=()
# retrieve all repositories and branches for CKF
REPOS_BRANCHES=($(yq -r '.applications[] | select(._github_repo_name) | [(._github_repo_name, ._github_repo_branch)] | join(":")' $BUNDLE_FILE | sort --unique))

# TODO: We need to not hardcode this and be able to deduce all images from the bundle
# https://github.com/canonical/bundle-kubeflow/issues/789
RESOURCE_DISPATCHER_BRANCH=track/1.0
RESOURCE_DISPATCHER_REPO=https://github.com/canonical/resource-dispatcher

for REPO_BRANCH in "${REPOS_BRANCHES[@]}"; do
  IFS=: read -r REPO BRANCH <<< "$REPO_BRANCH"
  git clone --branch $BRANCH https://github.com/canonical/$REPO
  cd $REPO
  IMAGES+=($(bash ./tools/get-images.sh))
  cd - > /dev/null
  rm -rf $REPO
done

# retrieve all repositories and branches for dependencies
DEP_REPOS_BRANCHES=($(yq -r '.applications[] | select(._github_dependency_repo_name) | [(._github_dependency_repo_name, ._github_dependency_repo_branch)] | join(":")' $BUNDLE_FILE | sort --unique))

for REPO_BRANCH in "${DEP_REPOS_BRANCHES[@]}"; do
  IFS=: read -r REPO BRANCH <<< "$REPO_BRANCH"
  git clone --branch $BRANCH https://github.com/canonical/$REPO
  cd $REPO
  # for dependencies only retrieve workload containers from metadata.yaml
  IMAGES+=($(find -type f -name metadata.yaml -exec yq '.resources | to_entries | map(select(.value.upstream-source != null)) | .[] | .value | ."upstream-source"' {} \;))
  cd - > /dev/null
  rm -rf $REPO
done

# manually retrieve resource-dispatcher
git clone --branch $RESOURCE_DISPATCHER_BRANCH $RESOURCE_DISPATCHER_REPO
cd resource-dispatcher
IMAGES+=($(bash ./tools/get-images.sh))
cd ..
rm -rf resource-dispatcher

# manually retrieve pipelines runner image to test pipelines
IMAGES+=($(echo "charmedkubeflow/pipelines-runner:ckf-1.8"))

# manually retrieve katib experiment image
IMAGES+=($(echo "docker.io/kubeflowkatib/simple-pbt:v0.17.0"))

# manually retrieve helloworld image to test knative
IMAGES+=($(echo "ghcr.io/knative/helloworld-go:latest"))

# manually retrieve tf-mnist-with-summaries image to test training operator
IMAGES+=($(echo "kubeflow/tf-mnist-with-summaries:latest"))

# ensure we only show unique images
IMAGES=($(echo "${IMAGES[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

# print full list of images
printf "%s\n" "${IMAGES[@]}"
