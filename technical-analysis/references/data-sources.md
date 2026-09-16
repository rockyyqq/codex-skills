# Data sources

Price history, from free endpoints that have been verified to work from this machine. Never
analyse from memory or from a remembered price.

## What to use

**Yahoo Finance chart API** - the workhorse. Covers Singapore, London, the United States,
Hong Kong and most indices.

```
https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1y&interval=1d
```

Symbol forms: `AAPL`, `1211.HK`, `ES3.SI`, `IWDA.L`, `^STI`, `000300.SS`, `399006.SZ`.

Two behaviours to know. It **throttles** after roughly twenty rapid requests, so space
calls out. And for very long ranges it silently returns **monthly** bars regardless of the
interval requested - so ask for a bounded window (`range=1y`, `range=5y`) rather than
`range=max`, or supply explicit `period1` and `period2` timestamps.

**Eastmoney kline** - Hong Kong and mainland listings, and the fallback when Yahoo does not
carry a symbol.

```
https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={market}.{code}
  &fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg={YYYYMMDD}&end={YYYYMMDD}
```

`market` is `116` for Hong Kong, `1` for Shanghai, `0` for Shenzhen. So BYD is
`116.01211`, the CSI 300 is `1.000300`, the ChiNext index `0.399006`.

Its sibling host `push2.eastmoney.com` blocks this address; `push2his` works, but
intermittently times out. Retry twice before treating a failure as real.

**Eastmoney fund API** - Chinese unit trusts and exchange-traded funds, quoted by NAV.

```
https://api.fund.eastmoney.com/f10/lsjz?fundCode={code}&pageIndex=1&pageSize=1500
```

Fallback when that times out: `http://fund.eastmoney.com/pingzhongdata/{code}.js` carries
the same series in a `Data_netWorthTrend` block.

**China Securities Index Company** - index levels and a price-earnings field for CSI
indices.

```
https://www.csindex.com.cn/csindex-home/perf/index-perf?indexCode=000300
  &startDate=YYYYMMDD&endDate=YYYYMMDD
```

Note that the field named `peg` carries a figure consistent with the index price-earnings
ratio and that no dividend-yield field is present. Treat the field name as unconfirmed.
Non-trading days are padded with the previous close, so a row count larger than the number
of trading days is expected.

## Reliable versus unreliable

| Source | Works | Notes |
|---|---|---|
| Yahoo chart API | Yes | Throttles; monthly bars on very long ranges |
| Eastmoney `push2his` kline | Yes, intermittently | Retry twice |
| Eastmoney fund API | Yes | NAV only, not price |
| CSIndex | Yes | Index level and a PE-type field |
| Eastmoney `push2` | **No** | Blocks this address |
| Yahoo `quoteSummary` | **No** | Returns 401 *Invalid Crumb* without a session cookie |

## A credentialed route: Futu / moomoo OpenD

Both broker SDKs connect to **OpenD** - a separate desktop application that holds the
broker session and serves quotes to the SDK over a local port. Neither SDK works without
it running and logged in, however the package is installed.

| | |
|---|---|
| Install | `pip install futu-api` (import `futu`) or `pip install moomoo-api` (import `moomoo`) |
| Gateway | OpenD, downloaded from the OpenAPI page of moomoo or Futu, logged in, left running |
| Endpoint | `127.0.0.1:11111` |
| Symbol form | `HK.01211`, `SH.000300`, `SZ.399006`, `US.AAPL`, `SG.ES3` |
| Probe | `scripts/opend_probe.py` |

Four things to know before relying on it.

**It needs normal permissions, not the restricted sandbox.** The SDK creates a log
directory under `AppData\Roaming` on import, so a sandboxed run fails at the import
before it reaches OpenD.

**Quote entitlements are per market.** Without a quote right the feed is delayed or
snapshot-only. Historical daily bars are generally available more freely than live ticks,
so check the entitlement before building anything on real-time data.

**It is local.** No external service is contacted, and nothing works while OpenD is
closed.

**The data is the broker's, not the exchange's.** Useful for consistency with what the
account sees, but it is a vendor feed and its history may differ slightly from the
exchange's own series.

**When it is worth the setup.** It is a steadier feed than the scraped sources for Hong
Kong and mainland names, and it can read the household's own positions rather than having
them retyped from screenshots. For daily-bar readings of the kind this skill produces it
adds nothing over the free sources - those update once a day.

### Verified working, 12 September 2026

| Symbol | Snapshot | Daily bars | Note |
|---|---|---|---|
| `HK.01211` (BYD) | Yes | Yes | Close 79.85, matches Yahoo and Sina exactly |
| `US.QQQ` | Yes | Yes | Close 714.88, matches Yahoo exactly |
| `SH.000300` | **No** | **No** | "No permission for A-share market index quotes" |
| `SG.ES3` | **No** | **No** | "No permission for Singapore market ETF quotes" |

So entitlements are per market and per instrument type, and they do not follow from having
an account. Hong Kong and US equity data came through; the A-share index and the Singapore
ETF did not. Check before designing anything around a symbol.

### Three traps in this interface

**`max_count` takes bars forward from the start date, not backward from today.** Asking for
`max_count=30` with `start=None` returns the *oldest* thirty bars of the default
one-year window - around a year stale - and the dates look plausible enough to pass a
glance. Request the whole window (`max_count=1000`, `start=None`) and take the most recent
bars from the end. Confirmed against the API: the same call returned 30 rows ending
2025-10-27, and 245 rows ending 2026-09-11.

**`get_cur_kline` needs an active subscription; `request_history_kline` does not.** Calling
the first without subscribing fails with "subscribe to KL_Day first". Prefer
`request_history_kline` for a one-off read.

**A batch call fails as a whole if any single symbol lacks an entitlement.** Asking for
four symbols in one snapshot returned one error naming one of them, hiding the state of the
other three. Query one symbol at a time when any of them might be unentitled.

## Index valuation - PE and dividend yield

The China Securities Index Company publishes daily price-earnings and dividend-yield figures
per index as an Excel file. This is the source that was missing for the longest: price
history tells you where an index has been, and only valuation tells you whether it is cheap.

```
https://oss-ch.csindex.com.cn/static/html/csindex/public/uploads/file/
    autofile/indicator/{index_code}indicator.xls
```

`scripts/valuation.py` reads it. Requires `pandas` and `xlrd`. Verified 12 September 2026,
about twenty daily rows per index:

| Index | Code | P/E total capital | P/E calc capital | D/P total | D/P calc |
|---|---|---:|---:|---:|---:|
| CSI 300 | `000300` | 14.74 | 16.94 | 2.61% | 2.32% |
| CSI Dividend Low Vol 100 | `930955` | 8.97 | 10.08 | 4.28% | 4.63% |
| CSI Dividend Low Vol | `H30269` | 8.23 | 7.93 | 4.22% | 4.77% |
| CSI 500 | `000905` | 28.97 | 30.96 | 1.36% | 1.23% |

**Two share-capital conventions, and they differ.** `P/E1` and `D/P1` use total share
capital; `P/E2` and `D/P2` use calculation share capital. For the CSI 300 that is 14.74
against 16.94 - a 15% gap. Mixing them silently changes the answer, so report which one is
in use.

**Earnings yield, not P/E, is what compares with a bond.** One divided by the P/E gives what
the index earns per unit of price: 6.78% for the CSI 300, 11.15% for the dividend low-vol
100. The P/E itself is a multiple and has nothing to be measured against.

**What this source does not give.** No price-to-book, and about a month of history rather
than a full series. It is a recent snapshot, so a percentile against its own past cannot be
computed from it alone.

**Still unsourced: the government bond yield** to compare the earnings yield against. The
Eastmoney curve endpoint answers, but returns coded column names rather than maturities, and
guessing which column is the ten-year would put an unverified number at the centre of the
comparison. Worth resolving deliberately or not at all.

## What the a-stock-data toolkit contributes

`simonlin1212/a-stock-data` (Apache-2.0, ~9.8k stars) is an A-share data skill with one idea
worth borrowing regardless of whether the toolkit itself is ever installed.

**Order sources by blocking risk, not by convenience.** Its documented principle: prefer
mootdx and Tencent for quotes, K-line, real-time price and market capitalisation because
they do not block; use Eastmoney only for data nothing else carries, and rate-limit every
call to it. That is exactly what happened here - Eastmoney refused four consecutive
connections in one session, and its `push2` host blocks this address outright.

**A failure must raise; it is never a zero.** Its integration notes record that a missing
file at the Shenzhen exchange returned a headers-only table, and that the implementation
raises rather than reading that as "every instrument has zero margin trading". The same rule
applies to every fetch in this skill: an empty result is something to report, not a zero to
compute with.

**Distinguish the request date from the data date.** Its verification table carries both,
because they differ - a Saturday request returns Friday's snapshot, and a month-end weights
file carries the month-end date.

## Telling a failure from a flat market

Three checks, in order:

1. **Did the response arrive at all?** A timeout or an HTTP error is a failure. Say which.
2. **Was the series returned in the granularity asked for?** Monthly bars when daily was
   requested is a silent failure and will produce a wrong answer rather than no answer.
3. **Does the last date match the last trading day?** A series ending three weeks ago is
   stale. Report the date with every figure.

**Always state the source and the as-of date in the output.** A price without a date is not
a fact about anything.

## What these sources do not give

- **Intraday history** beyond a short window.
- **Adjusted prices consistently.** Corporate actions - splits, rights issues, dividends -
  are handled differently by different endpoints. A price series that has not been adjusted
  for a split will show a fall that did not happen. Check for an unexplained gap before
  trusting a long series.
- **Volume that is comparable across markets.** Hong Kong and mainland volume conventions
  differ; a volume ratio within one series is meaningful, a comparison across markets is not.
