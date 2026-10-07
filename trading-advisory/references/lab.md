# The lab

Everything here is outside the family plan. Nothing in this file is a plan input.

## Where it lives

| Item | Path |
|---|---|
| Lab root | `D:\OneDrive\1 YUAN QI\1.1 Personal\4 AI-assistant\TradingLab\` |
| Tool source | `TradingLab\TradingAgents\` - shallow clone of `TauricResearch/TradingAgents`, Apache-2.0 |
| Runs and reports | `TradingLab\runs\` - where the household reads output |
| Run log and the wall | `TradingLab\README.md` |
| Python environment | `%LOCALAPPDATA%\tradinglab\venv\` - deliberately outside OneDrive, because a synced virtual environment wastes bandwidth and can corrupt itself |

The lab root is a sibling of `1 Family Plan`, not a subfolder of it. Keep it that way; the whole
arrangement depends on the two being separate things.

## State as installed

- `tradingagents` **0.5.2**, installed from the cloned source on 2 October 2026.
- Python **3.13.1** in the lab venv, created 2 October 2026.
- **No end-to-end run has been made yet**, because no language-model key has been supplied. The
  install succeeded; the pipeline is unverified. Say so in any note produced before the first
  successful run.

## What a run needs

**A model provider.** One of these, set in the lab's environment:

| Provider | Variable |
|---|---|
| OpenAI | `OPENAI_API_KEY` |
| Anthropic | `ANTHROPIC_API_KEY` |
| Google | `GOOGLE_API_KEY` |
| DeepSeek | `DEEPSEEK_API_KEY` |
| Qwen | `DASHSCOPE_API_KEY` or `DASHSCOPE_CN_API_KEY` |
| GLM (Zhipu) | `ZHIPU_API_KEY` or `ZHIPU_CN_API_KEY` |
| MiniMax | `MINIMAX_API_KEY` or `MINIMAX_CN_API_KEY` |
| Groq, Mistral, Moonshot, OpenRouter, NVIDIA, xAI | the matching `*_API_KEY` |
| A local model | no key needed - run Ollama and set `llm_provider: "ollama"` |

Optional: `FRED_API_KEY` for macro series, `ALPHA_VANTAGE_API_KEY` for a second price source,
`SEC_EDGAR_USER_AGENT` so the SEC can reach the household rather than the project.

**Where the data comes from.** Yahoo Finance for prices and for non-US statements, SEC EDGAR for US
filings, FRED for macro, StockTwits and Reddit for sentiment. This is the same free-data layer the
`technical-analysis` skill already documents - the tool is not distinctive in what it fetches, only
in what it does with it. Hong Kong (`.HK`) and mainland (`.SS`, `.SZ`) tickers are supported.

## Running a job

Point output at the lab so runs stay together:

```powershell
$env:TRADINGAGENTS_DATA_DIR = 'D:\OneDrive\1 YUAN QI\1.1 Personal\4 AI-assistant\TradingLab\runs'
```

Then either the interactive CLI (`tradingagents`, from the lab venv) or, for something repeatable, a
scripted run with the flags supplied up front:

```powershell
$env:TRADINGAGENTS_LLM_PROVIDER = 'openai'
$env:TRADINGAGENTS_QUICK_THINK_LLM = '<fast model>'
$env:TRADINGAGENTS_DEEP_THINK_LLM = '<reasoning model>'
& "$env:LOCALAPPDATA\tradinglab\venv\Scripts\tradingagents.exe" `
    --ticker 0941.HK --date 2026-10-02 `
    --analysts market,news,fundamentals `
    --save --no-show
```

Pin the model IDs rather than accepting a moving default, so the note can say what produced it. A
model name that resolves to something different next month makes the record worthless.

## What a run costs, and how to spend less

Every run spends tokens on the provider's account. The bill scales with the number of analysts, the
debate rounds, the risk rounds, and how much text each step reads. To spend less: fewer analysts, one
debate round, one risk round, a cheaper quick-think model, and a narrower question. Decide the budget
before a batch, not after.

## When a run fails

- **No key, or the wrong variable name for the chosen provider** - the run stops before it starts.
  This is the expected state until the household supplies one.
- **Started without a terminal and missing an answer** - the run stops and names the flag or variable
  to set. Set it rather than guessing.
- **Provider rate limits or timeouts** - retry, then record the failure as the run's outcome. A run
  that did not complete produced no view, and the note says that.
- **Data gaps.** Yahoo cannot date a statement by when it was published, so a past-dated run is told
  non-US statements are withheld rather than being served a figure that may not have existed yet.
  Treat a thin report as a data limit, not as a signal.

Record every failed run in the log too. A log that only contains successes is a backtest with the
losers deleted.

