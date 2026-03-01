from whatsapp_client import send_whatsapp_message
from firestore_helper import get_user_by_id, save_user_profile, find_user_by_name

async def handle_onboarding(user_id: str, text: str):
    """
    Handles the conversational onboarding flow for a new user.
    Uses Firestore (with in-memory fallback) to be stateful.
    """
    profile = get_user_by_id(user_id) or {}
    step = profile.get("onboarding_step", 0)
    lc_text = text.lower()

    # Start or restart onboarding
    if lc_text == 'start':
        profile = {"onboarding_step": 1}
        save_user_profile(user_id, profile)
        await send_whatsapp_message(user_id, "👋 Welcome! What's your full name?")
        return True, "restarted_onboarding"

    # Not in onboarding
    if step == 0:
        return False, "not_in_onboarding"

    # Step 1: Expecting name
    if step == 1:
        profile['name'] = text
        existing_user = find_user_by_name(text)
        if existing_user and existing_user.get('_id') != user_id:
            profile['onboarding_step'] = '1b_confirm_link'
            profile['existing_profile_id'] = existing_user['_id']
            save_user_profile(user_id, profile)
            await send_whatsapp_message(user_id, f"A profile for {text} already exists. Is this you? (yes/no)")
            return True, "asked_profile_link"

        profile['onboarding_step'] = 2
        save_user_profile(user_id, profile)
        await send_whatsapp_message(user_id, f"Nice to meet you, {text}! What role are you looking for?")
        return True, "asked_role"

    # Step 1b: Confirm linking to an existing profile
    if step == '1b_confirm_link':
        if lc_text == 'yes':
            # Here you would merge profiles or link them. For now, we'll just copy the old ID.
            # This is a placeholder for a more complex account linking logic.
            profile['linked_to'] = profile.get('existing_profile_id')
            profile['onboarding_step'] = 3 # Mark as complete
            save_user_profile(user_id, profile)
            await send_whatsapp_message(user_id, "Great! Your profile is linked. You can now search for jobs.")
            return True, "profile_linked"
        else:
            profile['onboarding_step'] = 2
            save_user_profile(user_id, profile)
            await send_whatsapp_message(user_id, "Okay. What role are you looking for?")
            return True, "asked_role_after_no_link"

    # Step 2: Expecting role
    if step == 2:
        profile['role'] = text
        profile['onboarding_step'] = 3 # Mark as complete
        save_user_profile(user_id, profile)
        await send_whatsapp_message(user_id, f"Excellent! I'll start finding jobs for a '{text}'. You can say 'search jobs' to begin.")
        return True, "onboarding_complete"

    # Already onboarded
    if step >= 3:
        return False, "already_onboarded"

    return False, "unknown_onboarding_state"
