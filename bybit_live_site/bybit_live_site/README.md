# Bybit Live Website

Разделение на:
- `frontend/index.html` — статический сайт для GitHub Pages
- `backend/main.py` — FastAPI backend, который безопасно запрашивает Bybit API

## Важно
GitHub Pages не исполняет Python. Backend нужно развернуть отдельно (например, Render), а статический frontend опубликовать на GitHub Pages.

## Backend (Render)
1. Загрузить весь проект в GitHub repo.
2. В Render создать Web Service из этого репозитория. Render может использовать `render.yaml`.
3. Build command: `pip install -r backend/requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Добавить Environment Variables: `BYBIT_API_KEY`, `BYBIT_API_SECRET`, `BYBIT_TESTNET=false`, `ALLOWED_ORIGINS=*` (для первичной проверки).
6. Использовать API key с Read-Only правами. Никогда не включать Trade/Withdraw.
7. После деплоя проверить `https://ТВОЙ-БЭКЕНД/health`.

## Frontend (GitHub Pages)
1. Загрузить `frontend/index.html` в корень репозитория или перенести его содержимое в существующий `index.html`.
2. В файле найти `const API_BASE = "https://YOUR-BACKEND-URL";` и заменить на URL backend, без `/` в конце.
3. Включить GitHub Pages в Settings → Pages.
4. Для production желательно заменить `ALLOWED_ORIGINS=*` в Render на точный origin сайта, например `https://username.github.io`.

## Что отображается
Открытые USDT linear perpetual позиции, unrealised PnL, ROI относительно initial margin, размер/номинал, цены, leverage, маржа, liquidation, TP/SL, wallet summary.

Это read-only мониторинг. Этот шаблон не включает spot, inverse, USDC и опционы.
