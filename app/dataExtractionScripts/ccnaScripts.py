#!/usr/bin/env python3
"""
Download only the DevOps-relevant CCNA course note files from
psaumur/CCNA_Course_Notes, without cloning the whole repository.

Usage:
    pip install requests
    python ccnaScripts.py

Files are saved into OpsMind/data/rawData/networking/<slug>/<file>
"""

from pathlib import Path

import requests

RAW_BASE = "https://raw.githubusercontent.com/psaumur/CCNA_Course_Notes/main/Course_Notes/"
REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = REPO_ROOT / "data" / "rawData" / "networking"

# Curated list: networking fundamentals + automation/cloud topics
# most relevant to a DevOps beginner (skips deep switching/routing-
# protocol internals like STP, VLAN trunking, OSPF/EIGRP/RIP configs).
FILES = [
    "Network_Devices.md",
    "OSI_Model_TCPSuite.md",
    "IPv4_Addressing_Part1.md",
    "IPv4_Addressing_Part2.md",
    "Subnetting_Part1.md",
    "Subnetting_Part2.md",
    "Subnetting_VLSM_Part3.md",
    "TCP_and_UDP.md",
    "DNS.md",
    "DHCP.md",
    "SSH.md",
    "NTP.md",
    "SYSLOG.md",
    "Standard_Access_Control_Lists.md",
    "Extended_Access_Control_Lists.md",
    "NAT_Static_Part1.md",
    "NAT_Dynamic_Part2.md",
    "Virtualizations_and_Cloud_Part1.md",
    "Virtualization_Containers.md",
    "Introduction_to_Network_Automation.md",
    "JSON_XML_YAML.md",
    "REST_APIs.md",
    "Software_Defined_Networking.md",
    "Ansible_Puppet_Chef.md",
]


def fetch_file(filename: str, session: requests.Session) -> None:
    slug = Path(filename).stem
    dest_dir = OUTPUT_ROOT / slug
    dest_path = dest_dir / filename

    url = RAW_BASE + filename
    resp = session.get(url, timeout=15)
    if resp.status_code == 200:
        resp.encoding = "utf-8"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path.write_text(resp.text, encoding="utf-8")
        print(f"[OK]      {filename}")
    else:
        print(f"[MISSING] {filename}  (HTTP {resp.status_code}) - check the path/branch")


def main() -> None:

    failed = 0
    fetched = 0
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    try:
        with requests.Session() as session:
            for filename in FILES:
                try:
                    fetch_file(filename, session)
                    fetched += 1
                except Exception as e:
                    failed += 1
                    print(f"Exception occured: {e}")
    except Exception as e:
        print(f"Exception occured: {e}")
    finally:
        print(f"Process completed. Files fetched succesfully: {fetched}. Files failed to be fetched: {failed}")
    


if __name__ == "__main__":
    main()