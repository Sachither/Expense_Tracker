from loguru import logger


def log_auth_event(
    event_type: str,
    email: str,
    success: bool,
    ip: str | None = None,
) -> None:
    """Log authentication events.

    Args:
        event_type: Type of event (login/logout)
        email: User's email
        success: Whether the event was successful
        ip: IP address of the client
    """
    status = "successful" if success else "failed"
    ip_info = f" from IP {ip}" if ip else ""
    logger.info(
        f"{event_type.capitalize()} {status} for user {email}{ip_info}",
    )
