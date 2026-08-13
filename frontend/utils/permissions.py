from utils.session import get_role


def is_admin() -> bool:
    return get_role() == "ADMIN"


def is_agent() -> bool:
    return get_role() == "CALL_CENTER"


def can_manage_users() -> bool:
    return is_admin()


def can_manage_documents() -> bool:
    return is_admin()


def can_view_reports() -> bool:
    return is_admin()


def can_view_audit_logs() -> bool:
    return is_admin()


def can_delete_cases() -> bool:
    return is_admin()
