import os, logging
logger = logging.getLogger(__name__)

# Prefer google.generativeai API-key flow
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except Exception:
    genai = None
    GENAI_AVAILABLE = False

# Vertex fallback (ADC)
try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    VERTEX_AVAILABLE = True
except Exception:
    vertexai = None
    VERTEX_AVAILABLE = False

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5')

if GENAI_AVAILABLE and GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        logger.info('Using google.generativeai with API key.')
    except Exception as e:
        logger.exception('Failed to configure google.generativeai: %s', e)

if VERTEX_AVAILABLE and not GENAI_AVAILABLE:
    try:
        vertexai.init(project=os.getenv('PROJECT_ID'), location=os.getenv('LOCATION', 'us-central1'))
        logger.info('Using Vertex AI SDK as fallback.')
    except Exception as e:
        logger.exception('Vertex init failed: %s', e)

def generate_gemini_reply(prompt: str) -> str:
    prompt = prompt or ''
    # lightweight intent detection
    low = prompt.lower()
    if any(w in low for w in ['apply to', 'search jobs', 'find jobs', 'generate resume']):
        return 'Understood — I can help with searching and applying to jobs. Try: "search jobs for data scientist" or "apply to job-1".'

    if GENAI_AVAILABLE and GEMINI_API_KEY:
        try:
            if hasattr(genai, 'generate_text'):
                resp = genai.generate_text(model=MODEL, prompt=prompt, max_output_tokens=256)
                if hasattr(resp, 'text') and resp.text:
                    return resp.text
                if hasattr(resp, 'candidates') and resp.candidates:
                    return getattr(resp.candidates[0], 'content', getattr(resp.candidates[0], 'text', ''))
            if hasattr(genai, 'generate'):
                resp = genai.generate(model=MODEL, input=prompt)
                if isinstance(resp, dict) and 'candidates' in resp and resp['candidates']:
                    return resp['candidates'][0].get('content') or resp['candidates'][0].get('text', '')
                return str(resp)
        except Exception as e:
            logger.exception('google.generativeai error: %s', e)
            return "Sorry — I couldn't generate a response via Gemini right now."

    if VERTEX_AVAILABLE:
        try:
            model = GenerativeModel(MODEL)
            gen = model.generate_content([prompt], generation_config=GenerationConfig(max_output_tokens=256))
            if hasattr(gen, 'text') and gen.text:
                return gen.text
            if hasattr(gen, 'candidates') and gen.candidates:
                c = gen.candidates[0]
                return getattr(c, 'content', getattr(c, 'text', ''))
            return 'No response from Vertex model.'
        except Exception as e:
            logger.exception('Vertex generate error: %s', e)
            return "Sorry — Gemini (Vertex) couldn't generate a reply right now."

    return 'Gemini not configured. Provide GEMINI_API_KEY or enable Vertex ADC.'