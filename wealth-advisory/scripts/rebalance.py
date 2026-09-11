#!/usr/bin/env python3
"""Allocation drift and rebalancing trade list.

The script does the arithmetic and follows the policy you give it. It does not
decide policy: account priority, bands, and minimum trade sizes all come from
the config, because those are the adviser's judgements, not the tool's.

Config keys
-----------
Required:
  policy.targets            {asset_class: fraction}; must sum to 1
  policy.region_targets     optional {region: fraction}; must sum to 1 if given
  accounts                  [{name, type, priority, holdings:[...]}]
Optional:
  currency                  default "SGD"
  policy.band_absolute      default 0.05  (+/- percentage points before a class breaches)
  policy.min_trade          default 0
  policy.max_asset_class    default none  - concentration limit, flagged if breached
  policy.max_holding        default none  - single-company limit; holdings marked
                              "diversified": true are exempt, everything else is treated
                              as a single name so a forgotten flag fails safe. Mark funds,
                              cash, and anything else that is not one company as well.
  (Region concentration limits live in portfolio_risk.py, which measures true
   look-through exposure rather than the tag on the listing.)
  new_contribution          {"amount": float, "account": str} - placed before any selling
  accounts[].transaction_cost_bps  default 0
  accounts[].locked         default false - flagged in the report (SRS, CPF-related)

holding: {"symbol": str, "asset_class": str, "value": float, "cost_basis": float (optional)}
Lower priority number means the account is used first.

Usage:
  python rebalance.py --config portfolio.json [--out report.md] [--json out.json]
"""

import argparse
import json
import sys
from pathlib import Path

EPSILON = 1.0


def die(message):
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


def load_config(path):
    if not Path(path).exists():
        die("Config file not found: {}".format(path))
    with open(path, "r", encoding="utf-8") as handle:
        try:
            return json.load(handle)
        except json.JSONDecodeError as exc:
            die("Config file {} is not valid JSON: {}".format(path, exc))


def money(value, currency):
    return "{} {:,.0f}".format(currency, value)


def pct(value):
    return "{:.1f}%".format(value * 100.0)


def load(cfg):
    if "policy" not in cfg or "targets" not in cfg["policy"]:
        die("Config needs policy.targets.")
    if "accounts" not in cfg:
        die("Config needs accounts.")

    targets = cfg["policy"]["targets"]
    total_target = sum(targets.values())
    if abs(total_target - 1.0) > 0.001:
        die(
            "policy.targets sum to {:.4f}, not 1.0. Fix the policy before rebalancing to it.".format(
                total_target
            )
        )
    if any(v < 0 for v in targets.values()):
        die("policy.targets contains a negative weight.")

    region_targets = cfg["policy"].get("region_targets")
    if region_targets:
        total_region = sum(region_targets.values())
        if abs(total_region - 1.0) > 0.001:
            die(
                "policy.region_targets sum to {:.4f}, not 1.0.".format(total_region)
            )

    current = {cls: 0.0 for cls in targets}
    for account in cfg["accounts"]:
        if "holdings" not in account or not account["holdings"]:
            die("Account {!r} has no holdings.".format(account.get("name", "?")))
        for holding in account["holdings"]:
            cls = holding.get("asset_class")
            if cls not in targets:
                die(
                    "Holding {!r} is tagged with asset class {!r}, which is not in "
                    "policy.targets. Add the class to the policy or retag the holding - "
                    "an untargeted class cannot be rebalanced.".format(
                        holding.get("symbol", "?"), cls
                    )
                )
            current[cls] += float(holding["value"])
    return targets, current


def region_exposure(cfg):
    totals = {}
    for account in cfg["accounts"]:
        for holding in account["holdings"]:
            region = holding.get("region")
            if region:
                totals[region] = totals.get(region, 0.0) + float(holding["value"])
    return totals


def plan(cfg, targets, current):
    accounts = cfg["accounts"]
    currency = cfg.get("currency", "SGD")
    contribution = cfg.get("new_contribution", {}).get("amount", 0.0)
    contribution_account = cfg.get("new_contribution", {}).get("account")

    total = sum(current.values())
    pool = total + contribution
    target_value = {cls: pool * weight for cls, weight in targets.items()}

    working = dict(current)
    changes = {cls: 0.0 for cls in targets}
    trades = []

    if contribution > 0:
        if not contribution_account:
            die("new_contribution needs an account name.")
        remaining = contribution
        while remaining > EPSILON:
            deficit = {c: target_value[c] - working[c] for c in targets}
            cls = max(deficit, key=deficit.get)
            if deficit[cls] <= EPSILON:
                break
            amount = min(remaining, deficit[cls])
            working[cls] += amount
            trades.append(
                {
                    "account": contribution_account,
                    "action": "Buy",
                    "asset_class": cls,
                    "amount": amount,
                    "reason": "New contribution",
                }
            )
            remaining -= amount

    guard = 0
    while guard < 5000:
        guard += 1
        over = {c: working[c] - target_value[c] for c in targets}
        under = {c: target_value[c] - working[c] for c in targets}
        over_cls = max(over, key=over.get)
        under_cls = max(under, key=under.get)
        if over[over_cls] <= EPSILON or under[under_cls] <= EPSILON:
            break
        amount = min(over[over_cls], under[under_cls])
        working[over_cls] -= amount
        working[under_cls] += amount
        changes[over_cls] -= amount
        changes[under_cls] += amount

    for cls in sorted(targets):
        delta = changes[cls]
        if abs(delta) <= EPSILON:
            continue
        if delta < 0:
            remaining = -delta
            for account in sorted(accounts, key=lambda a: a.get("priority", 99)):
                if remaining <= EPSILON:
                    break
                held = sum(
                    float(h["value"]) for h in account["holdings"] if h["asset_class"] == cls
                )
                if held <= EPSILON:
                    continue
                amount = min(held, remaining)
                trades.append(
                    {
                        "account": account["name"],
                        "action": "Sell",
                        "asset_class": cls,
                        "amount": amount,
                        "reason": "Above target",
                    }
                )
                remaining -= amount
        else:
            remaining = delta
            holders = [a for a in accounts if any(h["asset_class"] == cls for h in a["holdings"])]
            candidates = sorted(holders, key=lambda a: a.get("priority", 99)) or sorted(
                accounts, key=lambda a: a.get("priority", 99)
            )
            if not candidates:
                die("No accounts available to buy {}.".format(cls))
            account = candidates[0]
            trades.append(
                {
                    "account": account["name"],
                    "action": "Buy",
                    "asset_class": cls,
                    "amount": remaining,
                    "reason": "Below target",
                }
            )

    costs = {}
    for account in accounts:
        costs[account["name"]] = account.get("transaction_cost_bps", 0) / 10000.0
    for trade in trades:
        trade["cost"] = trade["amount"] * costs.get(trade["account"], 0.0)

    return {
        "currency": currency,
        "total": total,
        "pool": pool,
        "current": current,
        "regions": region_exposure(cfg),
        "target_value": target_value,
        "projected": working,
        "trades": trades,
        "total_cost": sum(t["cost"] for t in trades),
    }


def build_report(cfg, result):
    currency = result["currency"]
    targets = cfg["policy"]["targets"]
    band = cfg["policy"].get("band_absolute", 0.05)
    min_trade = cfg["policy"].get("min_trade", 0)
    total = result["total"]
    lines = []
    add = lines.append

    add("# Rebalancing worksheet")
    add("")
    add(
        "Total portfolio {}. Drift is measured against policy targets; a class breaches "
        "its band once it is more than {:.1f} percentage points away.".format(
            money(total, currency), band * 100.0
        )
    )
    add("")

    add("## Allocation against policy")
    add("")
    add("| Asset class | Target | Current | Drift | Dollars off target | In band? |")
    add("|---|---|---|---|---|---|")
    breaches = []
    for cls in sorted(targets):
        target_pct = targets[cls]
        current_pct = result["current"][cls] / total if total else 0.0
        drift = current_pct - target_pct
        gap = result["target_value"][cls] - result["current"][cls]
        breached = abs(drift) > band
        if breached:
            breaches.append(cls)
        add(
            "| {} | {} | {} | {} | {} | {} |".format(
                cls,
                pct(target_pct),
                pct(current_pct),
                ("{}{:.1f}%".format("+" if drift >= 0 else "", drift * 100.0)),
                money(gap, currency),
                "BREACHED" if breached else "ok",
            )
        )
    add("")
    if not breaches:
        add("Nothing is outside its band. Do not trade for the sake of trading - direct new contributions at the largest underweight instead.")
        add("")

    add("## Proposed trades")
    add("")
    if not result["trades"]:
        add("No trades proposed.")
    else:
        add("| Account | Action | Asset class | Amount | Est. cost | Reason |")
        add("|---|---|---|---|---|---|")
        for trade in result["trades"]:
            add(
                "| {} | {} | {} | {} | {} | {} |".format(
                    trade["account"],
                    trade["action"],
                    trade["asset_class"],
                    money(trade["amount"], currency),
                    money(trade["cost"], currency),
                    trade["reason"],
                )
            )
        add("")
        add("Total estimated transaction cost: **{}**.".format(money(result["total_cost"], currency)))
    add("")

    small = [t for t in result["trades"] if min_trade and t["amount"] < min_trade]
    if small:
        add(
            "{} proposed trade(s) fall below the {} minimum and are probably not worth "
            "executing on their own. Fold them into the next contribution instead.".format(
                len(small), money(min_trade, currency)
            )
        )
        add("")

    add("## Allocation after the proposed trades")
    add("")
    add("| Asset class | Before | After | Target |")
    add("|---|---|---|---|")
    for cls in sorted(targets):
        before = result["current"][cls] / total if total else 0.0
        after = result["projected"][cls] / result["pool"] if result["pool"] else 0.0
        add("| {} | {} | {} | {} |".format(cls, pct(before), pct(after), pct(targets[cls])))
    add("")

    region_targets = cfg["policy"].get("region_targets")
    if region_targets and result["regions"]:
        add("## Regional exposure (look-through, by holding tag)")
        add("")
        add(
            "Measured on the region tagged against each holding. If a fund holds assets "
            "elsewhere than its listing suggests, tag the holding with its underlying region "
            "so this table reflects what is actually owned."
        )
        add("")
        add("| Region | Target | Current | Drift | In band? |")
        add("|---|---|---|---|---|")
        for region in sorted(set(list(region_targets) + list(result["regions"]))):
            target = region_targets.get(region, 0.0)
            current = result["regions"].get(region, 0.0) / total if total else 0.0
            drift = current - target
            add(
                "| {} | {} | {} | {}{:.1f}% | {} |".format(
                    region,
                    pct(target),
                    pct(current),
                    "+" if drift >= 0 else "",
                    drift * 100.0,
                    "BREACHED" if abs(drift) > band else "ok",
                )
            )
        add("")

    max_class = cfg["policy"].get("max_asset_class")
    max_holding = cfg["policy"].get("max_holding")
    if max_class or max_holding:
        add("## Concentration limits")
        add("")
        add("| Limit | Largest | Actual | Limit | Result |")
        add("|---|---|---|---|---|")
        if max_class:
            cls = max(targets, key=lambda c: result["current"][c])
            actual = result["current"][cls] / total if total else 0.0
            add(
                "| Largest asset class | {} | {} | {} | {} |".format(
                    cls, pct(actual), pct(max_class), "PASS" if actual <= max_class else "**FAIL**"
                )
            )
        if max_holding:
            holdings = [
                (h.get("symbol", "?"), float(h["value"]))
                for account in cfg["accounts"]
                for h in account["holdings"]
                if not h.get("diversified", False)
            ]
            if holdings:
                symbol, value = max(holdings, key=lambda kv: kv[1])
                actual = value / total if total else 0.0
                add(
                    "| Largest single-company holding | {} | {} | {} | {} |".format(
                        symbol, pct(actual), pct(max_holding), "PASS" if actual <= max_holding else "**FAIL**"
                    )
                )
            else:
                add(
                    "| Largest single-company holding | none tagged | - | {} | n/a |".format(
                        pct(max_holding)
                    )
                )
        add("")


    locked = [a["name"] for a in cfg["accounts"] if a.get("locked")]
    if locked:
        add(
            "Locked accounts in this household: {}. Trades there cannot be reversed on the "
            "same terms as a brokerage account, so check the liquidity position before "
            "moving anything into them.".format(", ".join(locked))
        )
        add("")

    add(
        "Singapore note: there is no capital gains tax on an individual's disposal of "
        "investments, so a sale here is not automatically a taxable event. That is not a "
        "reason to trade freely - transaction costs are real, and the cash raised then has "
        "to be reinvested."
    )
    add("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Allocation drift and rebalancing trade list.")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", help="Write the markdown report here instead of stdout.")
    parser.add_argument("--json", dest="json_out", help="Also write raw results as JSON here.")
    args = parser.parse_args()

    cfg = load_config(args.config)
    targets, current = load(cfg)
    result = plan(cfg, targets, current)
    report = build_report(cfg, result)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(report)
        sys.stdout.write("Report written to {}\n".format(args.out))
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
