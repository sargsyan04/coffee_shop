import uuid

from fastapi import Request

GUEST_SESSION_KEY = "guest_session_id"


def get_or_create_guest_session_id(request: Request) -> str:
    session_id = request.session.get(GUEST_SESSION_KEY)

    if not session_id:
        session_id = uuid.uuid4().hex
        request.session[GUEST_SESSION_KEY] = session_id

    return session_id