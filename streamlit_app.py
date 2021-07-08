#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 10:37:26 2021

@author: Gilly
"""

## TFT API Streamlit app with riotwatcher package

import riotwatcher
import streamlit as st

def main():
    st.title('TFT API Exercise')
    st.markdown('''

        This streamlit app helps tft players find their best and worst
        units. We can also request basic visualizations about the
        distribution of our placements.  Place make sure your api key
        exists alone in a file called *apikey.txt*.
        * Libraries used: pandas, matplotlib, seaborn,
        [riotwatcher](https://riot-watcher.readthedocs.io/en/latest/),
        [streamlit](https://streamlit.io/).
        * Riot API can be found [here](https://developer.riotgames.com/)

    ''')

    ## Start page with only form to start riotwatcher Tftwatcher
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    ## Initial fields
    with st.form('Load Summoner Data'):
        name = st.text_input('Enter Summoner Name', key='name')
        region = st.selectbox(
            'Select region',
            ['na1', 'eu'],
            key='region')
        count = st.number_input(
            'Number of recent games',
            min_value=1,
            max_value=20,
            value=5,
            key='count')
        submit = st.form_submit_button('Request Data')
        if submit:
            st.session_state.submitted = True
            watcher = riotwatcher.TftWatcher(api_key=get_api_key())
            st.write(type(watcher))
            puuid, match_ids, matches = load_data(
                                                region,
                                                name,
                                                count,
                                                watcher)
            data = {
            'puuid':puuid,
            'summoner':name,
            'region':region,
            'match_ids':match_ids,
            'matches':matches
            }
            st.session_state.data = data
            if type(len(st.session_state.data['match_ids']))==int:
                st.write('Loaded '
                    + str(len(st.session_state.data['match_ids']))
                    + ' matches.')

def load_data(region, name, count, watcher):
    if region == 'na1':
        platform = 'americas'
    puuid = watcher.summoner.by_name(region, name)['puuid']
    match_ids = watcher.match.by_puuid(platform, puuid, count)
    matches = {}
    st.write(match_ids)
    for i in range(len(match_ids)):
        if i % 2 == 0:
            st.write(i)
        matches[match_ids[i]]=watcher.match.by_id(platform, match_ids[i])
    return puuid, match_ids, matches

def get_api_key():
    f = open('../apikey.txt', 'r')
    return f.read()

if __name__ == '__main__':
    main()
