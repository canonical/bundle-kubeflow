#!/usr/bin/env python3
"""
Generate SBOM-style artifact list from a Juju bundle YAML.

- Reads bundle YAML from a file path or STDIN
- Writes output to manifest.yaml by default (override with -o)
- Top-level clients.sbom.* fields are configurable via CLI flags
- service_url is a constant
- Choose which clients to apply to each artifact with --clients
"""

import sys
import argparse

try:
    import yaml
except ImportError:
    print("This script requires PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ---------- constants ----------
SERVICE_URL = "https://sbom-request.canonical.com"

SERIES_TO_BASE = {
    "focal": "ubuntu@20.04",
    "jammy": "ubuntu@22.04",
    "noble": "ubuntu@24.04",
}

# Render lists inline (flow style) for nicer `clients: ['sbom']` formatting
class FlowList(list):
    pass

def _flow_list_representer(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)

# IMPORTANT: register on SafeDumper because we use yaml.safe_dump
yaml.SafeDumper.add_representer(FlowList, _flow_list_representer)

# ---------- core ----------
def load_yaml(stream):
    return yaml.safe_load(stream)

def gen_artifacts(bundle: dict, clients_for_artifacts):
    """Create artifacts from bundle applications, deduped by charm name."""
    apps = (bundle or {}).get("applications", {})
    artifacts_by_name = {}

    for _, app in apps.items():
        charm_name = app.get("charm")
        if not charm_name:
            continue

        channel = app.get("channel")
        series = app.get("series")

        artifact = {
            "name": charm_name,
            "type": "charm",
            "clients": FlowList(list(clients_for_artifacts)),
        }
        if channel:
            artifact["channel"] = channel
        if series and series in SERIES_TO_BASE:
            artifact["base"] = SERIES_TO_BASE[series]

        if charm_name in artifacts_by_name:
            existing = artifacts_by_name[charm_name]
            # Keep first channel seen; enrich base if missing
            if "base" not in existing and "base" in artifact:
                existing["base"] = artifact["base"]
        else:
            artifacts_by_name[charm_name] = artifact

    return sorted(artifacts_by_name.values(), key=lambda x: x["name"])

def parse_clients_arg(s: str):
    parts = [p.strip() for p in s.split(",") if p.strip()]
    valid = {"sbom", "secscan"}
    unknown = [p for p in parts if p not in valid]
    if unknown:
        raise ValueError(f"Unknown client(s): {', '.join(unknown)} (valid: sbom, secscan)")
    if "sbom" not in parts:
        raise ValueError("At least 'sbom' must be included.")
    ordered = []
    if "sbom" in parts:
        ordered.append("sbom")
    if "secscan" in parts:
        ordered.append("secscan")
    return ordered

def main():
    parser = argparse.ArgumentParser(description="Generate artifact list YAML from a Juju bundle YAML.")
    parser.add_argument("bundle", nargs="?", help="Path to bundle YAML. If omitted, reads from STDIN.")
    parser.add_argument("-o", "--output", default="manifest.yaml", help="Output file path (default: manifest.yaml)")

    # Configurable clients.sbom fields
    parser.add_argument("--department", default="charm_engineering", help="clients.sbom.department")
    parser.add_argument("--email", default="your.email@canonical.com", help="clients.sbom.email")
    parser.add_argument("--team", default="analytics", help="clients.sbom.team")

    # Clients selection for artifacts
    parser.add_argument(
        "--clients",
        default="sbom",
        help="Comma-separated list of clients to assign to each artifact. "
             "Allowed: 'sbom' or 'sbom,secscan'. Default: sbom",
    )
    parser.add_argument(
        "--with-secscan",
        action="store_true",
        help="Shorthand for --clients sbom,secscan",
    )

    args = parser.parse_args()

    if args.with_secscan:
        clients_list = ["sbom", "secscan"]
    else:
        try:
            clients_list = parse_clients_arg(args.clients)
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(2)

    if args.bundle:
        with open(args.bundle, "r", encoding="utf-8") as f:
            bundle = load_yaml(f)
    else:
        bundle = load_yaml(sys.stdin)

    # Build top-level clients block dynamically
    clients_block = {
        "sbom": {
            "service_url": SERVICE_URL,  # constant
            "department": args.department,
            "email": args.email,
            "team": args.team,
        }
    }
    if "secscan" in clients_list:
        clients_block["secscan"] = {}

    output = {
        "clients": clients_block,
        "artifacts": gen_artifacts(bundle, clients_list),
    }

    with open(args.output, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            output,
            f,
            sort_keys=False,
            default_flow_style=False,
            allow_unicode=True,
            indent=2,
        )

    print(f"Wrote {args.output}")

if __name__ == "__main__":
    main()
