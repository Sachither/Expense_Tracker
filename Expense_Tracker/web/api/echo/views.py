from fastapi import APIRouter

from Expense_Tracker.web.api.echo.schema import Message

router = APIRouter()


@router.get("/", response_model=Message)
async def get_echo_message(message: str = "Hello!") -> Message:
    """
    Returns an echo message.

    :param message: message to echo (as query parameter).
    :returns: echo message.
    """
    return Message(message=message)


@router.post("/", response_model=Message)
async def send_echo_message(
    incoming_message: Message,
) -> Message:
    """
    Sends echo back to user.

    :param incoming_message: incoming message.
    :returns: message same as the incoming.
    """
    return incoming_message
