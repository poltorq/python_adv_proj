import os
from urllib.parse import urlencode
from datetime import datetime, timedelta

import httpx
from fastapi import FastAPI
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import select

from src.db.session import async_session
from src.db.user import User
from src.db.google_credentials import GoogleCredentials

app = FastAPI()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv(
    "GOOGLE_REDIRECT_URI", "https://turbomuza.ru/auth/google/callback"
)

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
]


@app.get("/auth/google")
async def start_auth(user_id: str, chat_id: str):
    print("\n=== START AUTH ===")
    print("telegram user_id:", user_id)

    state = f"{user_id}:{chat_id}"

    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }

    url = f"https://accounts.google.com/o/oauth2/auth?{urlencode(params)}"
    print("REDIRECT URL:", url)
    print("==================\n")

    return RedirectResponse(url)


@app.get("/auth/google/callback")
async def google_callback(
        code: str | None = None,
        state: str | None = None,
        error: str | None = None,
):
    print("\n=== GOOGLE CALLBACK ===")
    print("code:", code)
    print("state:", state)
    print("error:", error)

    if error:
        return JSONResponse({"error": error}, status_code=400)

    if not code or not state:
        return JSONResponse({"error": "missing code/state"}, status_code=400)

    try:
        user_id_str, chat_id_str = state.split(":")
        telegram_id = int(user_id_str)
        chat_id = int(chat_id_str)
    except Exception as e:
        print("❌ INVALID STATE:", state)
        return JSONResponse({"error": "invalid state"}, status_code=400)

    print("telegram_id:", telegram_id)
    print("chat_id:", chat_id)

    # --- exchange code → tokens ---
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )

    print("TOKEN STATUS:", resp.status_code)
    print("TOKEN BODY:", resp.text)
    resp.raise_for_status()

    tokens = resp.json()

    access_token = tokens["access_token"]
    refresh_token = tokens.get("refresh_token")
    scope = tokens.get("scope", "")
    token_type = tokens.get("token_type", "Bearer")
    expires_in = tokens.get("expires_in", 3600)
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()

        if not user:
            print("User not found → creating")
            user = User(
                telegram_id=telegram_id,
                google_connected=True,
            )
            session.add(user)
            await session.flush()
        else:
            user.google_connected = True

        result = await session.execute(
            select(GoogleCredentials)
            .where(GoogleCredentials.user_id == user.id)
        )
        creds = result.scalar_one_or_none()

        if creds:
            print("GoogleCredentials found → updating")
            creds.access_token = access_token
            creds.refresh_token = refresh_token
            creds.token_type = token_type
            creds.scope = scope
            creds.expires_at = expires_at
        else:
            print("GoogleCredentials not found → creating")
            creds = GoogleCredentials(
                user_id=user.id,
                access_token=access_token,
                refresh_token=refresh_token,
                token_type=token_type,
                scope=scope,
                expires_at=expires_at,
            )
            session.add(creds)

        await session.commit()

    print("✅ Credentials saved")

    print("bot token == ", BOT_TOKEN)

    # --- notify Telegram (ВАЖНО: chat_id) ---
    async with httpx.AsyncClient() as client:
        tg_resp = await client.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={
                "chat_id": chat_id,
                "text": (
                    "✅ Авторизация Google Calendar прошла успешно!\n\n"
                    "Теперь ты можешь работать с календарём 📅"
                ),
            },
        )

    print("TG STATUS:", tg_resp.status_code, tg_resp.text)
    print("=== AUTH FLOW DONE ===\n")

    return RedirectResponse(
        url=f"https://t.me/org_event_bot",
        status_code=302,
    )
