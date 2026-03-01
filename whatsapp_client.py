import os, logging, httpx
logger = logging.getLogger(__name__)

WHATSAPP_TOKEN = os.getenv('WHATSAPP_TOKEN')
PHONE_NUMBER_ID = os.getenv('PHONE_NUMBER_ID')
API_VERSION = os.getenv('WHATSAPP_API_VERSION', 'v23.0')

async def send_whatsapp_message(to: str, text: str) -> bool:
    if os.getenv("LOCAL_DEV") == "true":
        logger.info(f"LOCAL DEV: Message to {to}: {text}")
        return True

    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        logger.error('Missing WhatsApp credentials; message not sent.')
        return False
    url = f"https://graph.facebook.com/{API_VERSION}/{PHONE_NUMBER_ID}/messages"
    headers = {'Authorization': f'Bearer {WHATSAPP_TOKEN}', 'Content-Type': 'application/json'}
    payload = {'messaging_product': 'whatsapp', 'to': to, 'type': 'text', 'text': {'body': text}}
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(url, headers=headers, json=payload)
            logger.info('WhatsApp API response: %s %s', resp.status_code, resp.text)
            return resp.status_code in (200,201)
        except Exception as e:
            logger.exception('Error sending WhatsApp message: %s', e)
            return False