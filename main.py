import os
import logging
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn


from onboarding import handle_onboarding
from gemini_client import generate_gemini_reply
from whatsapp_client import send_whatsapp_message
from job_apply_service import search_jobs_for_role, apply_to_job, get_today_application_count

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_secure_token")

@app.get("/webhook")
async def verify_webhook(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(content=challenge, status_code=200)
    else:
        return JSONResponse(content={"error": "Forbidden"}, status_code=403)


@app.post('/webhook')
async def webhook(request: Request):
    payload = await request.json()
    logger.info('Webhook payload: %s', payload)

    try:
        entry = payload.get('entry', [])[0]
        changes = entry.get('changes', [])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
    except Exception:
        # Return 200 to prevent WhatsApp from retrying malformed/status payloads
        return JSONResponse(content={'status':'ignored'}, status_code=200)

    if not messages:
        return JSONResponse(content={'status':'invalid_payload'}, status_code=400)

    msg = messages[0]
    sender = msg.get('from')
    text = msg.get('text', {}).get('body', '').strip()

    # 1) Onboarding flow
    handled, reply = await handle_onboarding(sender, text)
    if handled:
        return JSONResponse(content={'status': 'ok'})

    lc = (text or '').lower()

    # 2) Job search
    if lc.startswith('search jobs') or lc.startswith('find jobs'):
        role = text.split('for')[-1].strip() if 'for' in lc else 'software engineer'
        results = search_jobs_for_role(role)
        for job in results[:5]:
            await send_whatsapp_message(sender, f"{job['title']} at {job['company']} — {job['apply_url']}")
        return JSONResponse(content={'status':'ok'})

    # 3) Apply
    if lc.startswith('apply to'):
        job_id = text.split('apply to')[-1].strip()
        success = apply_to_job(sender, job_id)
        if success:
            await send_whatsapp_message(sender, f"✅ Applied to job {job_id}")
        else:
            await send_whatsapp_message(sender, "❌ Could not apply; please try later.")
        return JSONResponse(content={'status':'ok'})

    # 4) Count of applications
    if lc.startswith('applied today') or lc.startswith('applied count'):
        count = get_today_application_count(sender)
        await send_whatsapp_message(sender, f"You applied to {count} job(s) today.")
        return JSONResponse(content={'status':'ok'})

    # 5) Fallback → Gemini AI
    try:
        ai_reply = await asyncio.to_thread(generate_gemini_reply, text)
    except Exception as e:
        logger.exception('Gemini call failed: %s', e)
        ai_reply = "Sorry, I couldn't process that right now."

    await send_whatsapp_message(sender, ai_reply)
    return JSONResponse(content={'status':'ok'})

@app.get("/healthz")
def healthz():
    return {"status": "ok"}