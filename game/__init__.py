import web
from web import tx
from sqlite3 import OperationalError, IntegrityError
from pathlib import Path
import json
from random import choice
import datetime as dt

from . import templates
from .templates import (
    render_game,
    render_games,
    render_players,
    render_started_waiter,
    render_entry,
    render_other_entries,
    get_character,
)


from . import util
from .util import *

ROUND_TIME_LIMIT = 180  # seconds


app = web.application(
    __name__,
    db=True,
    args={"p": "[\d]+", "player": "[ '-\w\d]+", "game": "[\d]+", "r": "[\d]+"},
    model={
        "games": {
            "progress": "TEXT NOT NULL"
        },  # one of waiting (for players), started, or finished
        "players": {
            "gameid": "INTEGER",
            "name": "TEXT NOT NULL",
            "character": "TEXT",
        },
        "landscapes": {
            "gameid": "INTEGER NOT NULL",
            "name": "TEXT NOT NULL",
        },
        "challenges": {
            "gameid": "INTEGER NOT NULL",
            "name": "TEXT NOT NULL",
        },
        "rounds": {
            "gameid": "INTEGER NOT NULL",
            "nth": "INTEGER PRIMARY KEY",  # nth entry in Python rounds list
            "start_time": "TEXT NOT NULL",
            "winner": "INTEGER",
            # FOREIGN KEY(winner) REFERENCES players(id)
        },
        "votes": {
            "gameid": "INTEGER NOT NULL",
            "round": "INTEGER NOT NULL",
            "player": "INTEGER NOT NULL",
            "voted_for": "INTEGER NOT NULL",
            # FOREIGN KEY(round) REFERENCES rounds(nth), FOREIGN KEY(player) REFERENCES players(id), FOREIGN KEY(voted_for) REFERENCES players(id),
        },
        "entries": {
            "gameid": "INTEGER NOT NULL",
            "round": "INTEGER NOT NULL",
            "player": "INTEGER NOT NULL",
            "writing": "TEXT NOT NULL",
            # FOREIGN KEY(player) REFERENCES player(rowid),
        },
    },
)

landscapes = {
    "hard streets of New York",
    "forest",
    "seashore",
    "farming village",
    "royal palace",
    "space station",
}

characters = {
    "tourist",
    "elf",
    "dwarf",
    "wizard",
    "witch",
    "blacksmith",
    "traveling peddler",
    "doctor",
    "prince",
    "princess",
    "ghost",
    "talking animal",
    "professor",
    "detective",
    "soldier",
    "astronaut",
    "philosopher",
    "painter",
    "chef",
    "time traveler",
}

challenges = {
    "There's a bear where it shouldn't be.",
    "Someone is missing their most cherished possession.",
    "Someone has been kidnapped.",
    "An outsider is manipulating people's opinions of the authorities.",
    "A stranger has come to live among you.",
    "A disease is spreading.",
    "A former friend or ally has grown cold and distant.",
}

rounds = [
    {
        "name": "exposition",
        "prompt": "Write about <b>your character</b>. What are they called, who are they, and how did they come to be in the 'landscape' for this story?",
    },
    {
        "name": "inciting incident",
        "prompt": "Write about an <b>incident</b>. This is the moment that kicks off the action of this story, and brings about the 'challenge' shown on this page.",
    },
    {
        "name": "rising action 1",
        "prompt": "Write about <b>increased tension</b>. What you write should build off the incident which won the last round, and should up the stakes or enhance the drama as a result of that incident.",
    },
    {
        "name": "rising action 2",
        "prompt": "Write about <b>a plan</b>. How will the characters resolve the 'challenge,' or at least attempt to do so? What aspects of the challenge stand in their way, and how could each of those aspects be overcome?",
    },
    {
        "name": "climax",
        "prompt": "Write about <b>the turning point</b>. The climax is the central moment in any story, where the characters and the challenge are pitted against each other.",
    },
    {
        "name": "falling action",
        "prompt": "Write about <b>the aftermath</b>. How do the characters act and feel after the climactic event? Tie up any loose ends, and resolve any additional conflicts.",
    },
    {
        "name": "resolution",
        "prompt": " Write about <b>what's next</b>. How has your character been changed by the experience of overcoming the challenge - or being overcome by it? Will more problems arise? If they arise, will your character help with those, too, or have they had enough?",
    },
]


def progress(game):
    with tx.db.transaction as cur:
        record = cur.select("games", what="rowid, *", where="rowid = ?", vals=[game])
        return record[0]["progress"]


def has_started(game):
    return progress(game) != "waiting"


def has_finished(game):
    return progress(game) == "finished"


def assign_characters(game):
    players = tx.db.select("players", what="rowid, *", where="gameid = ?", vals=[game])
    for p in players:
        c = choice(list(characters))  # reuse is OK?
        tx.db.update("players", character=c, where="rowid = ?", vals=[p["rowid"]])


def assign_landscape(game):
    c = choice(list(landscapes))
    tx.db.insert("landscapes", name=c, gameid=game)


def get_landscape(game):
    c = tx.db.select("landscapes", where="gameid = ?", vals=[game])
    return c[0]["name"]


def assign_challenge(game):
    # todo use player input
    c = choice(list(challenges))
    tx.db.insert("challenges", name=c, gameid=game)


def get_challenge(game):
    c = tx.db.select("challenges", where="gameid = ?", vals=[game])
    return c[0]["name"]


def get_rounds(game):
    rounds = tx.db.select(
        "rounds", what="rowid, *", order="nth DESC", where="gameid = ?", vals=[game]
    )
    return rounds


def get_current_round(game):
    r = tx.db.select(
        "rounds",
        what="rowid, *",
        order="nth DESC",
        limit=1,
        where="gameid = ?",
        vals=[game],
    )
    return int(r[0]["nth"]) if r else 0


def get_entries(game, rd):
    entry = tx.db.select(
        "entries",
        what="rowid, *",
        where="gameid = ? and round = ?",
        vals=[game, rd],
    )
    return entry


def get_entry(game, rd, player):
    entry = tx.db.select(
        "entries",
        what="rowid, *",
        where="gameid = ? and round = ? and player = ?",
        vals=[game, rd, player],
    )
    return entry


def get_other_entries(game, r, player):
    c = tx.db.select(
        "entries",
        what="rowid, *",
        where="gameid = ? and round = ? and player != ?",
        vals=[game, r, player],
    )
    return c


def get_player(game, pid):
    player = tx.db.select(
        "players", what="rowid, *", where="gameid = ? and rowid = ?", vals=[game, pid]
    )
    return player[0]


def get_players(game=None):
    if not game:
        players = tx.db.select("players", what="rowid, *", where="gameid is not null")
    else:
        players = tx.db.select(
            "players", what="rowid, *", where="gameid = ?", vals=[game]
        )
    return players


def who_has_voted(game, r):
    query = tx.db.select(
        "votes as v",
        what="v.gameid as gameid, v.round as round, v.player as player",
        where=f"v.gameid={game} and v.round={r}",
    )
    return [q["player"] for q in query]


def get_votes(game, r):
    query = tx.db.select(
        "votes as v",
        what="v.gameid as gameid, v.round as round, v.voted_for as voted_for, p.name as name, p.rowid as pid",
        join="players as p on v.voted_for=p.rowid",
        where=f"v.gameid={game} and v.round={r}",
    )
    if not query:
        return dict()
    result = {q["pid"]: 0 for q in query}
    for q in query:
        pid = q["pid"]
        result[pid] += 1
    return result, {q["pid"]: q["name"] for q in query}


def get_winner(game, r):
    q = tx.db.select(
        "rounds", what="winner", where="gameid = ? and nth = ?", vals=[game, r]
    )
    return q[0]["winner"]


def get_winning_entry(game, r):
    w = get_winner(game, r)
    if not w:
        raise ValueError(f"no winner for game {game}, round {r} yet")
    else:
        query = tx.db.select(
            "rounds as r",
            what="r.gameid, e.round, e.player, e.writing",
            join="entries as e on r.winner=e.player and r.nth=e.round and r.gameid=e.gameid",
            where="r.gameid = ? and e.round= ?",
            vals=[game, r],
        )
        return query[0]["writing"]


def get_possible_winners(votes):
    highest = max(votes.values())
    pw = []
    for name, num in votes.items():
        if num == highest:
            pw.append(name)
    return pw


def assign_winner(game, r):
    votes, _ = get_votes(game, r)
    pw = get_possible_winners(votes)
    if len(pw) == 1:
        w = pw[0]
    else:
        w = choice(pw)
    tx.db.update("rounds", winner=w, where="gameid = ? and nth = ?", vals=[game, r])
    return


def make_empty_entries(game, next_round):
    for player in get_players(game):
        tx.db.insert(
            "entries", gameid=game, player=player["rowid"], round=next_round, writing=""
        )


def advance(game):
    """Advance from the current round to the next round, or finish the game if the current round is the last round.
    Returns the page to which this function's caller should redirect players."""
    cr = get_current_round(game)
    if not cr:
        next_round = 1
        assign_characters(game)
        assign_landscape(game)
        assign_challenge(game)
        make_empty_entries(game, next_round)
        # extra time so players other than the one that started round are not penalized... hacky, but OK for now
        now = dt.datetime.now() + dt.timedelta(seconds=2)
        tx.db.insert("rounds", nth=next_round, start_time=now.isoformat(), gameid=game)

        return f"/games/{game}/rounds/1"
    elif cr == len(rounds):
        # game is over, show final screen
        return f"/games/{game}/story"
    else:
        next_round = cr + 1
        make_empty_entries(game, next_round)
        # extra time so players other than the one that started round are not penalized... hacky, but OK for now
        now = dt.datetime.now() + dt.timedelta(seconds=2)
        tx.db.insert("rounds", nth=next_round, start_time=now.isoformat(), gameid=game)
        return f"/games/{game}/rounds/{next_round}"


@app.control("")
class Home:
    def get(self):
        if "pid" in tx.user.session:
            raise web.SeeOther("/games")
        else:
            return app.view.home()


@app.control("players/create")
class CreatePlayer:
    def get(self):
        raise web.SeeOther("/")

    def post(self):
        name = web.form("name").name
        player = tx.db.insert("players", name=name)
        tx.user.session["name"] = name
        tx.user.session["pid"] = player
        raise web.SeeOther("/")


# @app.control("players/delete")
# class DeletePlayer:
#    def post(self):
#        tx.db.delete(
#            "players",
#            where="rowid = ?",
#            vals=[tx.user.session["pid"]],
#        )
#        # participants = tx.db.select(
#        #    "players", where="gameid = ?", vals=[tx.user.session["game"]]
#        # )
#        # if len(participants) == 0:
#        #    tx.db.delete("games", where="rowid = ?", vals=[tx.user.session["game"]])
#        tx.user.session = {}
#        raise web.SeeOther("/")


@app.control("games")
class Games:
    def get(self):
        if not tx.user.session.get("name"):
            raise web.SeeOther("/")
        games = tx.db.select("games", what="rowid, *", where="progress = 'waiting'")
        players = tx.db.select("players", what="rowid, *", where="gameid is not null")
        return app.view.games(games, players)


@app.control("games/{game}")
class Game:
    def get(self, game):
        # 404 if not exist
        # 'not started yet' if hasn't started
        # link you to current round if has started
        return f"game is {game}"


@app.control("games/create")
class CreateGame:
    def post(self):
        game = tx.db.insert("games", progress="waiting")
        current = tx.user.session.get("game")
        if not current:
            tx.db.update(
                "players", gameid=game, where="rowid = ?", vals=[tx.user.session["pid"]]
            )
            tx.user.session["game"] = str(game)
        raise web.SeeOther("/games")


@app.control("games/{game}/progress")
class GameStarted:
    def get(self, game):
        if tx.request.headers.get("hx-request"):
            if has_started(game):
                tx.response.headers["HX-Redirect"] = f"/games/{game}/rounds/1"
            else:
                pass
            return render_started_waiter(game)
        else:
            return "progress"  # todo but doesn't matter to player experience, this is an admin/plumbing route


@app.control("games/{game}/players")
class GamePlayers:
    def get(self, game):
        players = tx.db.select(
            "players", what="rowid, *", where="gameid = ?", vals=[game]
        )
        if tx.request.headers.get("hx-request"):
            # stripped view with only what HTMX needs
            return render_players(players, game)
        else:
            return app.view.players(game, players)


@app.control("games/{game}/join")
class JoinGame:
    def post(self, game):
        current = tx.user.session.get("game")
        if not current or current != game:
            tx.db.update(
                "players", gameid=game, where="rowid = ?", vals=[tx.user.session["pid"]]
            )
            tx.user.session["game"] = game
        else:
            # already in that game
            pass
        raise web.SeeOther("/games")


# @app.control("games/{game}/leave")
# class LeaveGame:
#    def post(self, game):
#        tx.db.update(
#            "players",
#            gameid=None,
#            where="rowid = ?",
#            vals=[tx.user.session["pid"]],
#        )
#        tx.user.session.pop("game")
#        raise web.SeeOther("/games")


@app.control("games/{game}/start")
class StartGame:
    def post(self, game):
        if has_started(game):
            raise web.SeeOther(f"/games/{game}/rounds/1")
        tx.db.update("games", progress="started", where="rowid = ?", vals=[game])
        raise web.SeeOther(advance(game))

    def get(self, game):
        raise web.SeeOther(f"/games/{game}/rounds/1")


@app.control("games/{game}/story")
class GameStory:
    def get(self, game):
        story = [get_winning_entry(game, r) for r in range(1, len(rounds) + 1)]
        return app.view.story(story)


@app.control("games/{game}/rounds")
class Rounds:
    def get(self, game):
        pass


@app.control("games/{game}/rounds/{r}")
class Round:
    def get(self, game, r):
        info = rounds[int(r) - 1]
        name = info["name"]
        prompt = info["prompt"]
        landscape = get_landscape(game)
        challenge = get_challenge(game)
        oe = get_other_entries(game, r, tx.user.session["pid"])
        if int(r) == 1:
            return app.view.round(r, name, prompt, landscape, challenge, oe, None)
        else:
            return app.view.round(
                r,
                name,
                prompt,
                landscape,
                challenge,
                oe,
                get_winning_entry(game, int(r) - 1),
            )


@app.control("games/{game}/rounds/{r}/advance")
class RoundAdvance:
    """Advance from round r to round r+1, or end the game."""

    def post(self, game, r):
        # TODO rewrite advance() to be less redundant with this post() method, or just fold it into this method completely
        # TODO use location header and Created (201) instead, in all places where I'm hackily using json.dumps for response to JS fetch
        cr = get_current_round(game)
        if cr == int(r):
            # round has not yet been advanced (by another player)
            redirect = advance(game)
            return {"next": redirect}

        else:
            q = int(r) + 1
            if q > len(rounds):
                return {"next": f"/games/{game}/story"}
            return {"next": f"/games/{game}/rounds/{q}"}

    def get(self, game, r):
        q = int(r) + 1
        if q > len(rounds):
            raise web.SeeOther(f"/games/{game}/story")
        raise web.SeeOther(f"/games/{game}/rounds/{q}")


@app.control("games/{game}/rounds/{r}/entries")
class Entries:
    def get(self, game, r):
        return app.view.entries(game, r, get_entries(game, r))


@app.control("games/{game}/rounds/{r}/entries/{p}/others")
class OtherEntries:
    def get(self, game, r, p):
        if not tx.request.headers.get("hx-request"):
            raise web.NotAuthorized
        d = []
        for oe in get_other_entries(game, r, p):
            # if i had more time would properly join entries with players
            other_player = oe["player"]
            other_name = get_player(game, other_player)["name"]
            d.append((other_name, oe["writing"]))
        return render_other_entries(game, r, p, d)


@app.control("games/{game}/rounds/{r}/entries/{p}")
class Entry:
    def post(self, game, r, p):
        writing = tx.request.body.get("writing")
        tx.db.update(
            "entries",
            writing=writing,
            where="gameid = ? and round = ? and player = ?",
            vals=[game, r, p],
        )
        raise web.Created(
            json.dumps({"entry": writing}), f"/games/{game}/rounds/{r}/entries/{p}"
        )

    def get(self, game, r, p):
        entry = get_entry(game, r, p)
        if tx.request.headers.get("hx-request"):
            # todo use 'during round' if requesting user has a pid that is in the same game... so they cant be sneaky
            return render_entry(p, entry)
        else:
            return app.view.entry(p, entry)


@app.control("games/{game}/rounds/{r}/timer")
class Timer:
    def get(self, game, r):
        start_time = tx.db.select(
            "rounds", what="start_time", where="gameid = ? and nth = ?", vals=[game, r]
        )[0]["start_time"]
        start_time = dt.datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S.%f")
        seconds_left = max(
            0,
            round(ROUND_TIME_LIMIT - (dt.datetime.now() - start_time).total_seconds()),
        )
        return json.dumps({"seconds": seconds_left})


@app.control("games/{game}/rounds/{r}/winner")
class RoundWinner:
    def post(self, game, r):
        w = get_winner(game, r)
        if w:
            raise web.SeeOther(f"/games/{game}/rounds/{r}/winner")
        else:
            assign_winner(game, r)
            raise web.SeeOther(f"/games/{game}/rounds/{r}/winner")

    def get(self, game, r):
        w = get_winner(game, r)
        votes, pid_to_name = get_votes(game, r)
        pw = get_possible_winners(votes)
        return app.view.winner(game, r, votes, pw, w, pid_to_name)


@app.control("/games/{game}/rounds/{r}/did-everyone-vote")
class DidEveryoneVote:
    def get(self, game, r):
        if get_winner(game, r):
            return {"ready": True}
        else:
            return {"ready": False}


@app.control("/games/{game}/rounds/{r}/waitforvotes")
class WaitForVotes:
    def get(self, game, r):
        votes, _ = get_votes(game, r)
        players = get_players(game)
        if sum(votes.values()) == len(players):
            return app.view.waitforvotes(game, r, True)
        else:
            return app.view.waitforvotes(game, r, False)


@app.control("games/{game}/rounds/{r}/votes")
class Votes:
    def post(self, game, r):
        voter = tx.user.session["pid"]
        voted_for = web.form("voted_for").voted_for
        already_voted = who_has_voted(game, r)
        if voter in already_voted:
            # ignore vote
            raise web.SeeOther(f"/games/{game}/rounds/{r}/waitforvotes")
        else:
            tx.db.insert(
                "votes", gameid=game, round=r, player=voter, voted_for=voted_for
            )
            raise web.SeeOther(f"/games/{game}/rounds/{r}/waitforvotes")

    def get(self, game, r):
        p = tx.user.session["pid"]
        info = rounds[int(r) - 1]
        name = info["name"]
        others = []
        for oe in get_other_entries(game, r, p):
            # if i had more time would properly join entries with players
            other_player = oe["player"]
            other_name = get_player(game, other_player)["name"]
            others.append(dict(id=other_player, name=other_name, writing=oe["writing"]))
        yours = get_entry(game, r, p)[0]["writing"]
        return app.view.votes(r, name, others, yours)


@app.control("waiter/games")
class WaiterGameList:
    """Render a list of games. This route is polled by HTMX to continually update part of the display on the /games page."""

    def get(self):
        games = tx.db.select("games", what="rowid, *", where="progress = 'waiting'")
        players = tx.db.select("players", what="rowid, *", where="gameid is not null")
        return render_games(games, players)
