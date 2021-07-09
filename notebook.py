import streamlit as st
import pandas as pd
import riotwatcher
from functions import *

watcher = riotwatcher.TftWatcher(api_key=get_api_key())
region = 'na1'
sum_id = watcher.summoner.by_name(region, 'ketelwon')['id']
league_id = watcher.league.by_summoner(region, sum_id)[1]['leagueId']
league_data = watcher.league.by_id(region, league_id)
sum_ids = []
for entry in league_data['entries'][:10]:
    sum_ids.append(entry['summonerId'])
st.write(sum_ids)
matches = {}
for id in sum_ids[:2]:
    puuid = watcher.summoner.by_id(region, id)['puuid']
    match_ids = watcher.match.by_puuid('americas', puuid, 2)
    sum_matches = {}
    for i in range(len(match_ids)):
        id = match_ids[i]
        temp_match = watcher.match.by_id('americas', id)
        sum_matches[id] = temp_match
    matches[puuid] = sum_matches
st.write(matches)
