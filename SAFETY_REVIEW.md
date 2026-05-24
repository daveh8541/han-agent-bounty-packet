# Wallet Safety Review — Han Solo Opportunity Fund

**Reviewer:** @jacksong2049-prog (JackAI)
**Date:** 2026-05-24
**Scope:** `agent.json`, `bounty.json`, `README.md`
**Micro-Bounty #2:** Wallet UX / Safety Review ($100–$500)

---

## Executive Summary

The Han Solo Opportunity Fund campaign has **strong baseline safety language**.
The policy covers the five essential topics (private keys, seed phrases, custody,
investment disclaimer, irreversible transfers) and explicitly prohibits agents
from making unauthorized transfers. However, I identified **3 medium-severity
gaps** related to spoofing risk, QR UX, and autonomous-agent guardrails.

| Category | Status | Risk |
|----------|--------|------|
| Investment disclaimer | ✅ Present | Low |
| No private keys policy | ✅ Present | Low |
| No seed phrase sharing | ✅ Present | Low |
| Custody disclosure | ✅ Present | Low |
| Irreversible transfer warning | ✅ Present | Low |
| Unauthorized transfer prohibition | ✅ Present | Low |
| Address spoofing protection | ⚠️ Partial | Medium |
| QR/copy UX safety | ⚠️ Missing | Medium |
| Autonomous-agent safeguards | ⚠️ Partial | Medium |

---

## Detailed Findings

### 1. Address Spoofing Risk — ⚠️ MEDIUM

**Issue:** The `agent.json` publishes raw crypto addresses without any
verification mechanism. An attacker who compromises the hosting (ngrok tunnel
or static site) could replace addresses with their own.

**Current state:**
```json
"funding_rails": [
  { "address": "bc1p7gwc3xcyfsn8jup..." },
  { "address": "0xd01792049ea8d3372a..." },
  { "address": "4NqGQrAaMyX8ieta9i..." }
]
```

**Recommendations:**
1. Add a PGP-signed or keybase-verified attestation for each address.
2. Publish a `addresses.sig` file alongside agent.json with Dave's signature.
3. Add a "Verify addresses before high-value transfers" notice (already partially present in safety array).
4. Consider a GitHub-hosted canonical copy as a secondary verification source.

### 2. QR / Copy UX Safety — ⚠️ MEDIUM

**Issue:** The safety policy mentions "QR/copy UX" in the bounty description
but the agent.json contains no structured UX safety guidance.

**Current state:** No UX safety section in agent.json.

**Recommendations:**
1. Add explicit UX safety requirements to agent.json:
   - QR codes must include the full address as visible text.
   - Copy buttons must trigger a visual confirmation.
   - A "Verify on block explorer" link should appear alongside every address.
2. Document the expected QR/copy UX behavior so agents can validate it.
3. Add a warning that QR codes can be tampered with at the rendering layer.

### 3. Autonomous-Agent Safeguards — ⚠️ MEDIUM

**Issue:** The safety policy prohibits unauthorized transfers but provides no
technical safeguards for autonomous agents that parse agent.json programmatically.

**Current state:**
```
"Agents must not make unauthorized transfers."
```

**Recommendations:**
1. Add a `safety.agent_guardrails` section:
   ```json
   "agent_guardrails": {
     "max_auto_transfer_usd": 0,
     "require_human_approval": true,
     "rate_limit_requests_per_hour": 60,
     "disallowed_operations": ["send", "transfer", "withdraw"]
   }
   ```
2. Publish a machine-readable safety policy (`safety.json`) that agents can
   validate against before taking action.
3. Add a `--dry-run` flag semantic that agents should respect.

### 4. ngrok Tunnel Reliability — ⚠️ LOW

**Issue:** The live campaign endpoint uses ngrok tunnels (`*.lhr.life`) which
expire. During review, the endpoint was unreachable. The GitHub repo serves
as a reliable fallback, but this should be documented.

**Recommendation:** Add a note that the GitHub repo (`daveh8541/han-agent-bounty-packet`)
is the canonical source when the live tunnel is down.

---

## What's Working Well

1. **Clear custody disclosure:** "Dave controls custody" is stated explicitly.
2. **Investment disclaimer:** Multiple places clarify this is not an investment.
3. **No private keys policy:** Repeated across all three files.
4. **Irreversible transfer warning:** Present and appropriately stern.
5. **Receipt policy:** The `receipt_policy` in agent.json provides structured
   accountability with required fields (date, mission_label, rail, amount, etc.).

---

## Verified Addresses

Using the Agent Rail Verifier (`verify_rails.py`):

| Network | Address (truncated) | Validation |
|---------|---------------------|------------|
| Bitcoin | `bc1p7gwc3xcy...` | ✅ Bech32m (P2TR/Taproot) — valid format |
| Ethereum | `0xd01792049e...` | ✅ EIP-55 checksum not present (all-lower) — valid format, recommend adding checksum |
| Solana | `4NqGQrAaMyX...` | ✅ Base58, 44 chars — valid format |

---

## Summary

The campaign has solid safety foundations. With the three recommendations above
(address signing, QR/UX guidance, and machine-readable agent guardrails), it
would be a strong example of safety-first agent funding infrastructure.

**Overall Safety Rating: 8/10** — Production-safe for manual human donations;
needs the above additions before it's safe for fully autonomous agent participation.
