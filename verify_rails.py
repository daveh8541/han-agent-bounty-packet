#!/usr/bin/env python3
"""
Agent Rail Verifier — Han Solo Opportunity Fund
Reads agent.json, validates crypto payment rails, verifies safety policies,
and generates a structured verification report.

Micro-Bounty #1: Agent Rail Verifier ($100–$250)
"""

import json
import sys
import re
import hashlib
from datetime import datetime, timezone

# ─── Address Validation ────────────────────────────────────────────────────

# Base58 alphabet (Bitcoin-style, also used by Solana)
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def validate_btc_bech32(address: str) -> dict:
    """Validate a Bitcoin bech32 (bc1...) address format."""
    result = {"valid": False, "network": "Bitcoin", "type": "unknown", "issues": []}

    if not address.startswith("bc1"):
        result["issues"].append("Does not start with 'bc1' (expected bech32 format)")
        return result

    # Length check: bech32 addresses are 42-62 chars for P2WPKH, longer for P2WSH
    if len(address) < 42 or len(address) > 90:
        result["issues"].append(f"Unusual length ({len(address)}); expected 42-90 chars for bech32")
        return result

    # Valid bech32 charset
    bech32_chars = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
    if not all(c.lower() in bech32_chars for c in address[3:]):
        result["issues"].append("Invalid characters in bech32 data portion")
        return result

    # SegWit version: bc1 + version byte (q=0, p=1)
    version_char = address[2].lower()
    if version_char == 'q':
        result["type"] = "P2WPKH (SegWit v0)"
    elif version_char == 'p':
        result["type"] = "P2TR (Taproot)"
    else:
        result["type"] = f"SegWit v{bech32_chars.index(version_char) if version_char in bech32_chars else '?'}"

    result["valid"] = True
    return result


def validate_eth_checksum(address: str) -> dict:
    """Validate an Ethereum/EVM address with EIP-55 checksum."""
    result = {"valid": False, "network": "Ethereum/EVM", "type": "unknown", "issues": []}

    if not address.startswith("0x"):
        result["issues"].append("Does not start with '0x'")
        return result

    if len(address) != 42:
        result["issues"].append(f"Incorrect length ({len(address)}); expected 42 chars")
        return result

    if not re.match(r'^0x[0-9a-fA-F]{40}$', address):
        result["issues"].append("Contains invalid hex characters")
        return result

    # EIP-55 checksum verification
    addr_lower = address[2:].lower()
    if address[2:] == addr_lower or address[2:] == addr_lower.upper():
        # All lower or all upper — no checksum, but valid format
        result["type"] = "EOA/Contract (no EIP-55 checksum)"
        result["valid"] = True
        result["issues"].append("No EIP-55 mixed-case checksum (address is all-lower or all-upper)")
    else:
        # Verify EIP-55 checksum
        h = hashlib.sha3_256(addr_lower.encode()).hexdigest()
        for i, c in enumerate(address[2:]):
            if c.isalpha():
                expected = c.upper() if int(h[i], 16) >= 8 else c.lower()
                if c != expected:
                    result["issues"].append(f"EIP-55 checksum mismatch at position {i+2}")
                    result["type"] = "INVALID CHECKSUM"
                    return result
        result["type"] = "EOA/Contract (EIP-55 verified)"
        result["valid"] = True

    return result


def validate_sol_base58(address: str) -> dict:
    """Validate a Solana base58 address format."""
    result = {"valid": False, "network": "Solana", "type": "unknown", "issues": []}

    # Solana addresses are 32-44 base58 characters
    if len(address) < 32 or len(address) > 44:
        result["issues"].append(f"Unusual length ({len(address)}); expected 32-44 base58 chars")
        return result

    if not all(c in BASE58_ALPHABET for c in address):
        result["issues"].append("Contains invalid base58 characters")
        return result

    result["type"] = "Solana account"
    result["valid"] = True
    return result


VALIDATORS = {
    "BTC": validate_btc_bech32,
    "ETH/EVM": validate_eth_checksum,
    "SOL/SPL": validate_sol_base58,
}


# ─── Rail Verification ─────────────────────────────────────────────────────

def verify_rails(agent_data: dict) -> dict:
    """Verify all funding rails in the agent.json."""
    rails = agent_data.get("funding_rails", [])
    results = []

    for rail in rails:
        symbol = rail.get("symbol", "UNKNOWN")
        address = rail.get("address", "")
        network = rail.get("network", "UNKNOWN")

        if symbol in VALIDATORS:
            result = VALIDATORS[symbol](address)
        else:
            result = {
                "valid": False,
                "network": network,
                "type": "unknown",
                "issues": [f"No validator available for {symbol}"]
            }

        result["symbol"] = symbol
        result["network_name"] = network
        result["address"] = address
        results.append(result)

    return {
        "total_rails": len(results),
        "valid_rails": sum(1 for r in results if r["valid"]),
        "invalid_rails": sum(1 for r in results if not r["valid"]),
        "rails": results,
    }


# ─── Safety Policy Check ───────────────────────────────────────────────────

REQUIRED_SAFETY_TOPICS = [
    "private keys",
    "seed phrase",
    "custody",
    "investment",
    "irreversible",
    "unauthorized",
]


def check_safety_policy(agent_data: dict) -> dict:
    """Check safety policy completeness against required topics."""
    safety_items = agent_data.get("safety", [])
    safety_text = " ".join(safety_items).lower()

    checks = {}
    for topic in REQUIRED_SAFETY_TOPICS:
        checks[topic] = topic.lower() in safety_text

    missing = [k for k, v in checks.items() if not v]
    all_covered = len(missing) == 0

    return {
        "all_covered": all_covered,
        "missing_topics": missing,
        "covered_topics": [k for k, v in checks.items() if v],
        "total_safety_items": len(safety_items),
        "safety_items": safety_items,
    }


# ─── Campaign Analysis ─────────────────────────────────────────────────────

def analyze_campaign(agent_data: dict) -> dict:
    """Analyze the campaign structure and metadata."""
    campaign = agent_data.get("campaign", {})
    tiers = agent_data.get("tiers", [])
    agents = agent_data.get("participating_agents", [])
    mission_labels = agent_data.get("accepted_mission_labels", [])

    return {
        "campaign_name": campaign.get("name", "Unknown"),
        "goal_usd": campaign.get("goal_usd", 0),
        "status": campaign.get("status", "Unknown"),
        "custody_model": campaign.get("custody", "Unknown"),
        "tiers": [
            {"name": t.get("name"), "usd": t.get("usd"), "receipt": t.get("receipt")}
            for t in tiers
        ],
        "participating_agents_count": len(agents),
        "participating_agents": agents,
        "mission_labels": mission_labels,
    }


# ─── Report Generation ─────────────────────────────────────────────────────

def generate_report(agent_data: dict) -> dict:
    """Generate a complete verification report."""
    rail_results = verify_rails(agent_data)
    safety_results = check_safety_policy(agent_data)
    campaign_analysis = analyze_campaign(agent_data)

    return {
        "report_metadata": {
            "generator": "Agent Rail Verifier v1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "schema": agent_data.get("schema", "unknown"),
        },
        "verdict": "PASS" if (rail_results["invalid_rails"] == 0 and safety_results["all_covered"]) else "REVIEW",
        "campaign": campaign_analysis,
        "rails": rail_results,
        "safety": safety_results,
    }


def print_report(report: dict):
    """Pretty-print the report to the console."""
    sep = "=" * 60
    print(sep)
    print("  🔍 Agent Rail Verifier — Han Solo Opportunity Fund")
    print(sep)
    print(f"  Generated: {report['report_metadata']['generated_at']}")
    print(f"  Schema:    {report['report_metadata']['schema']}")
    print(f"  Verdict:   {report['verdict']}")
    print()

    c = report["campaign"]
    print("  📋 Campaign")
    print(f"     Name:        {c['campaign_name']}")
    print(f"     Goal:        ${c['goal_usd']:,} USD")
    print(f"     Status:      {c['status']}")
    print(f"     Custody:     {c['custody_model'][:80]}...")
    print(f"     Agents:      {c['participating_agents_count']} ({', '.join(c['participating_agents'])})")
    print()

    r = report["rails"]
    print(f"  💰 Funding Rails ({r['valid_rails']}/{r['total_rails']} valid)")
    for rail in r["rails"]:
        icon = "✅" if rail["valid"] else "❌"
        print(f"     {icon} {rail['symbol']:8s} | {rail['network_name']:20s} | {rail['type']}")
        for issue in rail.get("issues", []):
            print(f"        ⚠️  {issue}")
    print()

    s = report["safety"]
    print(f"  🛡️  Safety Policy (items: {s['total_safety_items']}, all_covered: {s['all_covered']})")
    for topic in REQUIRED_SAFETY_TOPICS:
        icon = "✅" if s.get("covered_topics") and topic in s["covered_topics"] else "❌"
        print(f"     {icon} {topic}")
    print()
    print(f"  📄 Full safety items:")
    for item in s["safety_items"]:
        print(f"     • {item}")
    print(sep)


def main():
    """Entry point: read agent.json and run verification."""
    agent_json_path = "agent.json"

    try:
        with open(agent_json_path, "r") as f:
            agent_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: {agent_json_path} not found. Run from the repo root.", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {agent_json_path}: {e}", file=sys.stderr)
        sys.exit(1)

    report = generate_report(agent_data)
    print_report(report)

    # Output JSON report for machine consumption
    json_report_path = "rail-verification-report.json"
    with open(json_report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n  📄 Machine-readable report saved to: {json_report_path}")

    # Exit with non-zero if review is needed
    if report["verdict"] != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
