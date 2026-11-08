"""Official SDK Streamable HTTP transport using Arena's participant credentials."""
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from urllib.parse import urlsplit
from .catalog import CATALOG
from .challenges import list_challenges
from .models import Action, ArenaError, StartSession


def build_mcp(arena):
    origin = arena.settings.public_url.rstrip('/')
    mcp = FastMCP('Jaeger Arena', stateless_http=True, json_response=True, streamable_http_path='/',
                  instructions='Use your participant token. Read challenge controls before acting. Keep request IDs stable for retries; fetch current state after a revision conflict. No games are installed yet. Skill practice requires an independent evaluator.',
                  transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=True,
                      allowed_hosts=[urlsplit(origin).netloc], allowed_origins=[origin]))

    def principal(ctx):
        request = ctx.request_context.request
        if request is None:
            raise ArenaError(401, 'HTTP participant credentials required')
        auth = request.headers.get('authorization', '')
        return arena.authenticate(auth[7:] if auth.lower().startswith('bearer ') else '', mcp=True)

    @mcp.tool()
    def arena_me(ctx: Context) -> dict:
        """Read your identity, practice level, XP, rank, and bound participant ID."""
        p = principal(ctx)
        return arena.get_profile(p.participant_id, p)

    @mcp.tool()
    def arena_list_challenges(ctx: Context) -> dict:
        """Discover availability, versions, tiers, controls, and review/XP policies."""
        principal(ctx)
        return {'challenges': list_challenges()}

    @mcp.tool()
    def arena_skill_tree(ctx: Context) -> dict:
        """Read the extensible skill catalogue; declared avatar traits are not earned mastery."""
        principal(ctx)
        return CATALOG

    @mcp.tool()
    def arena_start_session(challenge_id: str, request_id: str, configuration: dict, ctx: Context, skill_id: str | None = None) -> dict:
        """Start an available challenge as yourself. configuration requires revision; model, tools and skill_revision are optional. Future games use this lifecycle."""
        p = principal(ctx)
        return arena.start(p, StartSession(participant_id=p.participant_id, challenge_id=challenge_id,
                                           request_id=request_id, configuration=configuration, skill_id=skill_id))

    @mcp.tool()
    def arena_session(session_id: str, ctx: Context) -> dict:
        """Get your session's state, available controls, revision, event log, and review."""
        return arena.session(principal(ctx), session_id)

    @mcp.tool()
    def arena_act(session_id: str, action: str, request_id: str, expected_revision: int, ctx: Context, payload: dict | None = None) -> dict:
        """Apply a control with its advertised input_schema as payload. record_note takes {note: text}; submit/cancel take {}. Reuse identical request_id/input on retries. Stale revisions fail without applying an action."""
        return arena.act(principal(ctx), session_id, Action(action=action, request_id=request_id,
                                                           expected_revision=expected_revision, payload=payload or {}))

    @mcp.tool()
    def arena_history(ctx: Context) -> dict:
        """Read your most recent 25 sessions and their reviews. This does not expose other participants' private logs."""
        p = principal(ctx)
        return {'sessions': arena.history(p, p.participant_id)}

    return mcp
