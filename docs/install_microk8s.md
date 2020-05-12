## 1. Overview
Kubeflow is a novel open source tool for Machine Learning workflow orchestration on kubernetes. It has great powers, but deploying it may not be so easy, depending on how and where you deploy your kubernetes. 
This tutorial will show you an easy way to deploy kubeflow using microk8s, a lightweight version of kubernetes, in a few simple steps.

### What you'll learn

* How to deploy microk8s on ubuntu
* How to deploy kubeflow using microk8s
* How to access your kubeflow dashboard 

### What you'll need
* Desktop or Virtual Machine with Ubuntu 16.04 or above
* A minimum of 4 CPU, 14GB RAM, 50GB Disk (recommended 8 CPU, 32GB RAM, 60GB Disk)
* Hyper V, if using multipass on a Windows machine (not available on Windows 10 Home)
* Some basic command-line knowledge

## 2. Open ubuntu terminal

All we need to do here is access the terminal of the machine we want to deploy kubeflow to. This is fairly straightforward.

### Option 1: on ubuntu machine

1. Open terminal (CTRL + Alt + t )

### Option 2:  accessing remote ubuntu virtual machine

1. Spin up a virtual machine with Ubuntu (on a server or cloud)

2. Access the machine terminal using `ssh`:

 `$ ssh ubuntu@<machine-ip-address>`

### Option 3: on Windows or MacOS 

1. Download multipass from *multipass.run* 

2. Launch Multipass instance with enough requirements:

`$ multipass launch --name kubeflow --mem 16G --disk 50G --cpus 4`

3. Access Multipass instance:

`$ multipass shell kubeflow`


## 3. Install Microk8s 

In this step you will install MicroK8s, a minimal, lightweight Kubernetes you can run and use on practically any machine. It can be installed with a snap:



1.  Install Microk8s: 

`$ sudo snap install microk8s --classic`

2. Verify installation:

`$ sudo microk8s status --wait-ready`


## 4. Join admin group

MicroK8s creates a group to enable seamless usage of commands which require admin privilege. 


1. To add your current user to the group and gain access to the  `.kube`  caching directory, run the following two commands:

` sudo usermod -a -G microk8s $USER `

`sudo chown -f -R $USER ~/.kube`

2. Exit and re-enter the session for permissions to take effect.


## 5. Deployment

Finally we are able to deploy all the kubernetes services behind kubeflow. To do this we just need to: 

1. Deploy kubernetes services:

`$ microk8s.enable dns dashboard storage`  

2. Deploy kubeflow using:

`$ microk8s.enable kubeflow`

3. Wait several minutes for all the services to be deployed, let's not interrupt the process. We can follow the process with the following command: 
`microk8s.kubectl get all --all-namespaces`

4. Congratulations!! We have made it! We can see the following prompt:

**![|535px;x293px;](https://lh6.googleusercontent.com/0buLbrbCZ0VAh7ZTNBcmuPfUQRc7JNEeiAVDGQ5JgGubrx_H9iwYFfTMrvsY7FNfwcxSNj6Ko0uX03SW_GOcvMktNRlMy250rB4PaOn1xMQG8qJH6llTHNw6JiQrNTv1sKkRYd0Dysk)**

## 6. Access kubeflow dashboard

Once deployed, now it is time to access the kubeflow dashboard, so we play around with it. 

### Option 1: on ubuntu desktop
If running ubuntu locally, now we simply need to open a new browser window and access the link given in the previous step. In our example, this link is:

`http://10.64.140.43.xip.io/`

### Option 2: on a VM or multipass
If running ubuntu on a virtual machine somewhere else, we need to create a SOCKS PROXY. This can be done as follows:

1. `Logout` from current session

2. Re-establish  connection to the machine using `ssh`, enabling SOCKS proxy. Examples:

`$ ssh -D9999 ubuntu@<machine_public_ip>`



`$ ssh -D9999 multipass@<machine_public_ip>` 

3. On your computer, go to `Settings > Network > Network Proxy`, and enable SOCKS proxy pointing to:  `127.0.0.1:9999`

4. On a new browser window, access the link given in the previous step. In our example, this link is:

`http://10.64.140.43.xip.io/`

## 7. That's all! Enjoy kubeflow! 

Congratulations! 

To know more about kubeflow visit: 
* kubeflow.org
* ubuntu.com/kubeflow

For further help, visit:
* ubuntu.com/kubeflow/consulting
