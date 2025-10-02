class EventSourceResponse:
    """
    Minimal no-op stub to satisfy optional import from mcp.server.sse
    when SSE transport is not used. If invoked, it behaves as an
    empty ASGI app that immediately returns.
    """

    def __init__(self, *args, **kwargs) -> None:  # pragma: no cover
        pass

    async def __call__(self, scope, receive, send):  # pragma: no cover
        return None

