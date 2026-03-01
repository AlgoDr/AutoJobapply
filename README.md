Phase 3 Job Agent (zip delivered)
--------------------------------
Files included:
- main.py: FastAPI webhook entrypoint
- onboarding.py: conversational onboarding (checks Firestore by name)
- gemini_client.py: Gemini integration (google.generativeai API-key preferred, Vertex fallback)
- firestore_helper.py: Firestore access with in-memory fallback
- whatsapp_client.py: sends WhatsApp messages via WhatsApp Business API
- job_apply_service.py: job search/apply placeholders + application logging
- requirements.txt, Dockerfile

Environment variables to set on Cloud Run:
- WHATSAPP_TOKEN, PHONE_NUMBER_ID, PROJECT_ID, LOCATION, GEMINI_API_KEY (optional), GCS_BUCKET (optional)

How to use:
- Deploy to Cloud Run with the env vars set.
- Send WhatsApp Business webhook messages to /webhook (Facebook/Meta will POST structured payloads)
- Onboard by sending 'start', then reply with your full name.
- If a Firestore profile exists with that name, you'll be asked to bind it; otherwise a minimal profile is saved.
- Commands: 'search jobs for <role>', 'apply to <job-id>', 'applied today'

Notes:
- Firestore and Google Cloud credentials: this code will attempt to use ADC. If ADC is not available it falls back to an in-memory store (good for local testing).
- Gemini: set GEMINI_API_KEY to use the google.generativeai API key flow. Vertex AI can be used as a fallback if configured.\n