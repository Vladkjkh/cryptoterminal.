import os
from decimal import Decimal
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pybit.unified_trading import HTTP

load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY", "").strip()
API_SECRET = os.getenv("BYBIT_API_SECRET", "").strip()
TESTNET = os.getenv("BYBIT_TESTNET", "false").lower() == "true"
ALLOWED_ORIGINS = [
    x.strip() for x in os.getenv("ALLOWED_ORIGINS", "*").split(",") if x.strip()
]

app = FastAPI(title="Bybit Live Positions API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ALLOWED_ORIGINS == ["*"] else ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

def D(value: Any) -> Decimal:
    try:
        return Decimal(str(value or "0"))
    except Exception:
        return Decimal("0")

def api():
    if not API_KEY or not API_SECRET:
        raise HTTPException(status_code=503, detail="Bybit API keys are not configured on the server")
    return HTTP(
        testnet=TESTNET,
        api_key=API_KEY,
        api_secret=API_SECRET,
        recv_window=10000,
    )

def checked(response, label):
    if not isinstance(response, dict) or response.get("retCode") != 0:
        msg = response.get("retMsg", "Unknown Bybit API error") if isinstance(response, dict) else str(response)
        raise HTTPException(status_code=502, detail=f"{label}: {msg}")
    return response.get("result", {})

@app.get("/health")
def health():
    return {"ok": True, "service": "bybit-live-positions"}

@app.get("/api/dashboard")
def dashboard():
    client = api()
    try:
        # USDT linear perpetual positions, with pagination.
        positions = []
        cursor = None
        while True:
            params = {"category": "linear", "settleCoin": "USDT", "limit": 200}
            if cursor:
                params["cursor"] = cursor
            result = checked(client.get_positions(**params), "Positions")
            positions.extend(result.get("list", []))
            cursor = result.get("nextPageCursor") or ""
            if not cursor:
                break

        positions = [p for p in positions if D(p.get("size")) > 0 and p.get("side")]
        wallet_result = checked(
            client.get_wallet_balance(accountType="UNIFIED", coin="USDT"),
            "Wallet balance",
        )
        accounts = wallet_result.get("list", [])
        wallet = accounts[0] if accounts else {}

        output_positions = []
        total_pnl = Decimal("0")
        total_value = Decimal("0")
        total_margin = Decimal("0")

        for p in positions:
            size = D(p.get("size"))
            value = abs(D(p.get("positionValue")))
            pnl = D(p.get("unrealisedPnl"))
            margin = D(p.get("positionIM"))
            leverage = D(p.get("leverage"))
            if margin <= 0 and leverage > 0:
                margin = value / leverage
            roi = (pnl / margin * 100) if margin > 0 else None

            total_pnl += pnl
            total_value += value
            total_margin += margin

            output_positions.append({
                "symbol": p.get("symbol"),
                "side": p.get("side"),
                "size": str(size),
                "positionValue": str(value),
                "entryPrice": p.get("avgPrice"),
                "markPrice": p.get("markPrice"),
                "unrealisedPnl": str(pnl),
                "roiPercent": str(roi) if roi is not None else None,
                "leverage": p.get("leverage"),
                "positionIM": str(margin),
                "liqPrice": p.get("liqPrice"),
                "takeProfit": p.get("takeProfit"),
                "stopLoss": p.get("stopLoss"),
                "curRealisedPnl": p.get("curRealisedPnl"),
                "cumRealisedPnl": p.get("cumRealisedPnl"),
                "tradeMode": p.get("tradeMode"),
                "updatedTime": p.get("updatedTime"),
            })

        return {
            "ok": True,
            "category": "USDT linear perpetual",
            "updatedAt": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "summary": {
                "openPositions": len(output_positions),
                "totalUnrealisedPnl": str(total_pnl),
                "totalPositionValue": str(total_value),
                "totalInitialMargin": str(total_margin),
                "roiOnInitialMargin": str(total_pnl / total_margin * 100) if total_margin > 0 else None,
                "equity": wallet.get("totalEquity"),
                "walletBalance": wallet.get("totalWalletBalance"),
                "availableBalance": wallet.get("totalAvailableBalance"),
                "accountPerpUPL": wallet.get("totalPerpUPL"),
            },
            "positions": output_positions,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Bybit request failed: {str(exc)}")
