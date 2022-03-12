import re
import web
from web import tx

__all__ = [
    "tx",
    "render_game",
    "render_games",
    "render_players",
    "render_started_waiter",
    "render_entry",
    "render_other_entries",
    "get_character",
    "titlecase",
    "get_winning_entry",
    "get_winner",
]


def get_winner(game, r):
    w = tx.db.select(
        "rounds", what="winner", where="gameid = ? and nth = ?", vals=[game, r]
    )
    return w[0]["winner"] if w else None


def get_winning_entry(game, r):
    w = get_winner(game, r)
    if not w:
        raise ValueError(f"no winner for game {game}, round {r} yet")
    else:
        query = tx.db.select(
            "rounds as r",
            what="r.gameid, e.round, e.player, e.writing",
            join="entries as e on r.winner=e.player and e.round=r.nth and e.gameid=r.gameid",
            where=f"r.gameid={game} and e.round={r}",
        )
        return query


def get_character(game, pid):
    query = tx.db.select(
        "players",
        what="rowid, character",
        where="gameid = ? and rowid = ?",
        vals=[game, pid],
    )
    try:
        return query[0]["character"]
    except IndexError:
        return None


def render_entry(player, entry, during_round=True):
    if during_round:
        words = entry.split()
        return f"{player} has written {len(words)} words."
    else:
        return f"{player} wrote: {entry}"


def render_other_entries(game, r, p, entries, during_round=True):
    if during_round:
        template = (
            f"<div id=other-entries hx-get=/games/{game}/rounds/{r}/entries/{p}/others hx-trigger='every 2s'>"
            + "{}</div>"
        )
    else:
        template = "<div id=other-entries>{}</div>"
    if not entries:
        return template.format("")
    result = []
    for name, writing in entries:
        result.append(render_entry(name, writing, during_round))
    return template.format("".join(result))


def render_game(gid):
    return f"<a href=/games/{gid}>{gid}</a>"


def render_games(games, players):
    if not games:
        return "<div id=games hx-swap=outerHTML hx-get=/waiter/games hx-trigger='every 2s'>Waiting for a game to start...</div>"
    result = []
    result.append("<p>These games are waiting for more players:</p>")
    result.append("<ol>")
    for game in games:
        iidd = game["rowid"]
        people = [p for p in players if p["gameid"] == iidd]
        li, unli = "<li>", "</li>"
        x = li
        x += f"{render_game(iidd)} {render_players(people, iidd)}</form>"
        if len(people) < 3:
            x += f" <form method=post action=/games/{iidd}/join><button>Join</button>"
        else:
            # bug: only shows up for last player who joined, not all players in this game - but not crucial to change that
            x += f"<form method=post action=/games/{iidd}/start><button>Start the Game</button></form>"
        x += unli
        result.append(x)
    result.append("</ol>")
    return "".join(result)


def render_players(ps, gid):
    template = (
        f"<span id='players-{gid}' hx-get=games/{gid}/players hx-trigger='every 2s'>"
        + "{}</span>"
    )
    if not ps:
        return template.format("")
    ps = [p["name"] for p in ps]
    return template.format(", ".join(ps))


def render_started_waiter(game):
    return f"<div style='visibility: hidden;' hx-get=/games/{game}/progress hx-trigger='every 2s'></div>"


def titlecase(s):
    return re.sub(r"[A-Za-z]+('[A-Za-z]+)?", lambda mo: mo.group(0).capitalize(), s)
