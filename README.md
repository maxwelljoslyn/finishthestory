# Finish the Story

Finish the Story is a writing game that anyone can play. This collaborative, online learning experience will help you practice the craft of creative writing.

The game plays out over several rounds. In every round, each player responds to a prompt with a chunk of writing that could be incorporated into the ongoing story. After the round timer runs out, the players vote on whose writing should get added.

## Screenshot

This screenshot illustrates the voting mechanic.

<img width="600vw" src="/game/static/screenshot.jpg">

## Install Your Own

If you want to run Finish the Story on your own web server, follow these instructions:

1. `git clone git@github.com:maxwelljoslyn/finishthestory.git`
2. `cd finishthestory`
3. `poetry install`
4. `poetry run web serve game:app --port XXXX`

If XXXX is not port 80, configure your reverse proxy to forward incoming requests to port XXXX.

## Credits

The original Finish the Story board game was developed by Achi Mishra, Chen Ji, Alison Crosby, Kendra Shu, Raghu Mina, and Keyu Lai.

This (prototype) web adaptation of the board game was implemented by Maxwell Joslyn. It has all the functionality of the original, though the UI is still bare-bones.
