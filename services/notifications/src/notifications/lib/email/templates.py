"""Short transactional email templates with no diary content."""

from __future__ import annotations


def verification_email(link: str) -> tuple[str, str]:
    """Return subject and text for email verification."""
    return (
        "Confirme seu email",
        "Use o link abaixo para confirmar seu email. Ele expira em 24 horas.\n\n"
        f"{link}\n\nSe você não criou uma conta, ignore esta mensagem.",
    )


def reset_email(link: str) -> tuple[str, str]:
    """Return subject and text for password reset."""
    return (
        "Redefinição de senha",
        "Use o link abaixo para definir uma nova senha. Ele expira em 30 minutos.\n\n"
        f"{link}\n\nSe você não solicitou, ignore esta mensagem.",
    )
