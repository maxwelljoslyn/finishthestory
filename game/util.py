def get_players(gameid):
    """Return players playing in  `gameid`."""
    return tx.db.select("players", what="rowid, *", where="gameid = ?", vals=[gameid])


def get_winner(gameid, in_round):
    """Return winner of round `in_round` for game `gameid`."""
    pass


def get_story(gameid):
    """Join all the winning submsissions so far, so players can view them while writing, or read complete story at the end of the game."""
    pass


def validate_vote(player, voted_for, current_round):
    """Player should be a rowid so they can be compared to other rowids,"""
    # todo
    if player == voted_for:
        # can't vote for yourself
        # return error, "can't vote for yourself"
        pass
    if current_round != 1:
        # can't vote for previous winner
        last_winner = get_winner(current_round - 1)
        if voted_for == last_winner:
            # return error, "can't vote last winner"
            pass
    else:
        # player can vote for anyone
        pass
