# Finish the Story

Finish the Story is a writing game that anyone can play. This collaborative, online learning experience will help you practice the craft of creative writing.

## Play Online

[https://story.maxwelljoslyn.com](https://story.maxwelljoslyn.com) hosts an online demo of Finish the Story.

## Install Your Own

If you want to run Finish the Story on your own web server, follow these instructions:

1. `git clone git@github.com:maxwelljoslyn/finishthestory.git`
2. `cd finishthestory`
3. `poetry install`
4. `poetry run web serve game:app --port XXXX`

If XXXX is not port 80, configure your reverse proxy to forward incoming requests to port XXXX.

## Credits

The original Finish the Story board game was developed by Achi Mishra, Chen Ji, Alison Crosby, Kendra Shu, Raghu Mina, and Keyu Lai.

The web adaptation of the board game was implemented by Maxwell Joslyn.
