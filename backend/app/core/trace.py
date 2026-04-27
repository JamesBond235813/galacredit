import contextvars
import uuid


trace_id_ctx_var: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")


def get_trace_id() -> str:
    return trace_id_ctx_var.get()


def set_trace_id(value: str) -> contextvars.Token:
    return trace_id_ctx_var.set(value)


def reset_trace_id(token: contextvars.Token) -> None:
    trace_id_ctx_var.reset(token)


def new_trace_id() -> str:
    return uuid.uuid4().hex
