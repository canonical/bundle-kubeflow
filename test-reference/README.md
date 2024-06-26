# Test reference versions

This directory contains a `versions.json` file that can be used as reference for combining versions of different components to test the Charmed Kubeflow bundle.

It follows this schema:

```json
{
  "ckf-version-risk-mlflow-version-risk": {
	"ckf":"",
	"mlflow": "",
	"k8s": {
       	  "charmed-kubernetes": {
            "min-supported": "",
            "max-supported": ""
    	  },
    	  "microk8s": {
            "min-supported": "",
            "max-supported": ""
    	  },
    	  "aks": {
            "min-supported": "",
            "max-supported": ""
    	  },
    	  "eks": {
            "min-supported": "",
            "max-supported": ""
  	  }
	},
	"juju": {
          "current": "",
  	  "future": ""
	}
  },
}
```

where,

* `ckf` and `mlflow` define the versions of each bundle to deploy
* A `k8s` substrate is a type of Kubernetes the team desires to test on (e.g. Microk8s, or AKS)
    * The `min-supported` is the smallest version the bundle should be tested on 
    * The `max-supported` is the latest version the bundle should be tested on
* The `current` juju version is the latest supported version of juju the MLOps team uses in the CI
* The `future` juju version is the target version to be supported

## Usage

Each object in "ckf-version-risk-mlflow-version-risk" can be combined to form te environment in which the bundle will be tested. For example `ckf 1.8/stable, mlflow 2.0/stable, on charmed-kubernetes 1.29 and juju 3.4/stable`.
