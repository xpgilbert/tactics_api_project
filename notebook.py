import streamlit as st
import pandas as pd
import riotwatcher
from functions import *
import json
if st.button('rewrite json'):
    watcher = riotwatcher.TftWatcher(api_key=get_api_key())
    region = 'na1'
    sum_id = watcher.summoner.by_name(region, 'ketelwon')['id']
    league_id = watcher.league.by_summoner(region, sum_id)[1]['leagueId']
    league_data = watcher.league.by_id(region, league_id)
    sum_ids = []
    for entry in league_data['entries'][:10]:
        sum_ids.append(entry['summonerId'])
    # st.write(sum_ids)
    summoners = {}
    for id in sum_ids:
        puuid = watcher.summoner.by_id(region, id)['puuid']
        match_ids = watcher.match.by_puuid('americas', puuid, 2)
        sum_matches = {}
        for i in range(len(match_ids)):
            id = match_ids[i]
            temp_match = watcher.match.by_id('americas', id)
            sum_matches[id] = temp_match
        summoners[puuid] = sum_matches
    st.write('Loaded '+ str(len(summoners.keys())) + ' summoners.')
    ## Create JSON FILE
    if st.button('Send it'):
        with open('summoners_test.json', 'w') as outfile:
            json.dump(summoners, outfile)

## For testing, load json file
with open('summoners_test.json') as f:
    summoners = json.load(f)

## Find all unique matches:
unique_ids = []
unique_matches = {}
for summoner in summoners.values():
    for match in summoner.values():
        match_id = match['metadata']['match_id']
        if match_id not in unique_ids:
            unique_ids.append(match_id)
            unique_matches[match_id] = match
## get all units and placements from every unique match
data = {'matches':unique_matches, 'match_ids':unique_ids}
df = get_units_data(data, only=False)
df = score_units(df)
st.write(df)


if st.button('show '):
    st.write('show something')
