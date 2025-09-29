# Generating SBOMs with Scripts

This document explains how to generate SBOMs for bundles, charms, and snaps using the provided Python scripts and `sbomber`.

---

## Prerequisites

Before starting, ensure the following:

* Setup Canonical VPN.
* Install and setup `sbomber` according to its instructions: [sbomber documentation](https://sbom-request.canonical.com/docs).
* Familiarize yourself with how `sbomber` works.

---

## Step 1: Identify Products for SBOM Generation

For the 25.10 cycle, SBOMs were generated for:

* Kubeflow bundle
* MLflow bundle
* Feast charms
* DSS snap

---

## Step 2: Prepare Bundle Files

1. Place the bundle file in the working folder.
2. Transform the bundle file into a `manifest.yaml` containing SBOM artifacts:

```bash
./generate_sbom_artifacts.py bundle.yaml --clients sbom --email your.email@canonical.com
```

**Notes:**

* `--clients` specifies which clients to use. Supported clients are `sbom` and `secscan`. You can specify both with `--clients sbom,secscan`. Default is `sbom`.
* Always provide your email.
* After this step, `manifest.yaml` will be generated in the folder.

---

## Step 3: Non-Bundle Components

If you are generating SBOMs for non-bundle components (e.g., individual charms or snaps), you should manually create your own `manifest.yaml`.

For reference and inspiration, see:
[Charm SBOM manifest example](https://github.com/canonical/observability/blob/main/ssdlc-manifests/charm-sbom-manifest.yaml)

---

## Step 4: Prepare SBOM Artifacts

Run the `sbomber` prepare command:

```bash
./sbomber prepare manifest.yaml
```

---

## Step 5: Submit SBOM Requests

Submit SBOM generation requests (this step may take hours for large bundles):

```bash
./sbomber submit
```

---

## Step 6: Poll for Completion

Poll until all charms in `manifest.yaml` are ready. You will receive email notifications for each charm:

```bash
./sbomber poll --wait --timeout 240
```

---

## Step 7: Download SBOMs

Once SBOM generation is complete, download the SBOMs:

```bash
./sbomber download --reports-dir=./sbomber-reports/
```

All generated SBOMs will be stored in the `./sbomber-reports/` directory.
