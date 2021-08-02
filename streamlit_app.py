#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jul  7 10:37:26 2021

@author: Gilly
"""

## TFT API Streamlit app with riotwatcher package

import riotwatcher
import streamlit as st
import json
from os import path
from functions import *

def main():
    st.title('TFT API Exercise')
    st.markdown('''
        This streamlit app helps tft players find their best and worst
        units. Place make sure your api key
        exists in the directory above this python file in a file called
        *apikey.txt*.
        * Libraries used: os, pandas, json, sklearn,
        [riotwatcher](https://riot-watcher.readthedocs.io/en/latest/),
        [streamlit](https://streamlit.io/).
        * Riot API can be found [here](https://developer.riotgames.com/)
    ''')
    ## Check for apikey.txt file
    # if not st.secrets('apikey'):
    #     st.write('There is not an apikey in the streamlit secrets.')
    # if not path.exists('../apikey.txt'):
    #     with st.form('apikey_file'):
    #         st.markdown('''
    #             *You do not have an apikey.txt file in the directory
    #             above this app.  Please either use this widget to create
    #             one or add it manually.  Then refresh this page.*
    #         ''')
    #
    #         apikey = st.text_input('Enter API Key', type = 'password')
    #         if st.form_submit_button('Write apikey.txt file'):
    #             with open('../apikey.txt', 'w') as f:
    #                 f.write(apikey)
    #     apikey = 0
    #     st.stop()
    ## Select from sideback
    explore_options = ['Summoner Data','League Data']
    exploring = st.sidebar.radio(
        label = 'What are we exploring today?',
        options = explore_options
        )
    if exploring == explore_options[0]:
        by_summoner()
    if exploring == explore_options[1]:
        by_league()
########################################################################
########################################################################
########################################################################
## By summoner
def by_summoner():
    ## Start page with only form to start riotwatcher.TftWatcher
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    ## Initial fields
    with st.form('Load Summoner Data'):
        st.markdown('''
        We can explore individual summoner data in this section
        of the app.  This analyzes across all queue types.
        ''')
        name = st.text_input('Enter Summoner Name', key='name')
        region = st.selectbox(
            'Select region',
            ['na1', 'eu'],
            key='region'
            )
        count = st.number_input(
            'Number of recent games',
            min_value=1,
            max_value=20,
            value=10,
            key='count'
            )
        submit = st.form_submit_button('Request Summoner Data')
        if submit:
            st.session_state.submitted = True
            watcher = riotwatcher.TftWatcher(api_key=get_api_key())
            if 'watcher' not in st.session_state:
                st.session_state.watcher = watcher
            data = load_summoner_data(region, name, count, watcher)
            st.session_state.data = data
            if type(len(st.session_state.data['match_ids']))==int:
                st.write('Loaded '
                    + str(len(st.session_state.data['match_ids']))
                    + ' matches.')
    ## Show desired data
    if st.session_state.submitted:
        data_options = [
            'End of Match Data',
            'Winning Units',
            'Losing Units',
            'First Place Units',
            'Eighth Place Units'
            ]
        select = st.selectbox('Select what data to show', data_options)
        only = st.selectbox('Only the desired summoner', ['Yes', 'No'])
        only = [True, False][['Yes', 'No'].index(only)]
        if (select == data_options[0]) and (only == False):
            group = st.checkbox('Sort by summoner')
        if select in data_options[1:5]:
            n_units = st.number_input(
                'How many units',
                key='unit_count',
                min_value=1,
                max_value=10,
                value=3)
            raw_data = st.checkbox('Show raw data', key='raw_data')
        show_data = st.button('Show Data')
        if show_data:
            data = st.session_state.data
            ## End of Match Data
            if select == data_options[0]:
                df = get_endings_dataframe(data, only)
                ## Get summoner names for only = False
                if only == False:
                    with st.spinner('Getting all summoners info'):
                        watcher = riotwatcher.TftWatcher(api_key=get_api_key())
                        for puuid in df['puuid']:
                            sum = watcher.summoner.by_puuid(region, puuid)['name']
                            df.loc[df['puuid']==puuid, 'summoner'] = sum
                    if group:
                        df = df.sort_values(by='summoner')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['summoner', 'placement']]
                    cols = ['summoner', 'placement'] + cols
                    df = df[cols]
                df = df.drop('puuid', axis=1)
                st.write(df)
            ## Winning Units
            elif select == data_options[1]:
                df = get_units_data(data, only)
                units = score_units(df)
                st.write(
                'These are the top ' +
                str(n_units) +
                ' winning units from the last ' +
                str(count) +
                ' games:')
                st.write(units[:n_units][['score']])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units)
            ## Losing Units
            elif select == data_options[2]:
                df = get_units_data(data,only)
                units = score_units(df)
                st.write(
                    'These are the worst ' +
                    str(n_units) +
                    ' losing units from the last ' +
                    str(count) +
                    ' games:')
                st.write(units.sort_values(by='score')[:n_units][['score']])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units.sort_values(by='score', ascending=True))
            ## First Place Units
            elif select == data_options[3]:
                df = get_units_data(data,only)
                units = score_units(df)
                if 1 not in units.columns.tolist():
                    error = 'ERROR: no units got first place in this search'
                    return st.write(error)
                st.write(
                    'These are the ' +
                    str(n_units) +
                    ' units that placed first most often in the last ' +
                    str(count) +
                    ' games:')
                st.write(units[:n_units])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units)
            ## Eighth Place Units
            elif select == data_options[4]:
                df = get_units_data(data,only)
                units = score_units(df)
                if 8 not in units.columns.tolist():
                    error = 'ERROR: no units got eighth place in this search'
                    return st.write(error)
                st.write(
                    'These are the ' +
                    str(n_units) +
                    ' units that placed eighth most often in the last ' +
                    str(count) +
                    ' games:')
                st.write(units.loc[group_by[8] == group_by[8].max()][:n_units][[8]])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units.sort_values(by='score', ascending=True))
## By league
def by_league():

    ## Start page with only form to start riotwatcher.TftWatcher
    if 'submitted' not in st.session_state:
        st.session_state.submitted = False
    with st.form('Initialize league data'):
        st.markdown('''
        We can explore ranked league data in this section
        of the app.  Hyper Roll functionality will be added later. You
        have the option to save the loaded league data as a json to
        analyze later without having to reload the data from the API
        every time.
        ''')
        name = st.text_input('Enter Summoner Name', key='name')
        # queue = st.selectbox(
        #     label='Queue Type',
        #     options=['Ranked','Hyper Roll']
        #     )
        region = st.selectbox(
            'Select region',
            ['na1', 'eu'],
            key='region'
            )
        count = st.number_input(
            'Number of recent games per summoner',
            min_value=1,
            max_value=20,
            value=2
            )
        # queue = ['RANKED_TFT', 'RANKED_TFT_TURBO'][['Ranked', 'Hyper Roll'].index(queue)]
        submit = st.form_submit_button('Request League Data')
        if submit:
            st.session_state.submitted = True
            watcher = riotwatcher.TftWatcher(api_key=get_api_key())
            if 'watcher' not in st.session_state:
                st.session_state.watcher = watcher
            data = load_league_data(region, name, count, watcher)
            st.session_state.data = data
            if type(len(st.session_state.data['match_ids']))==int:
                st.write('Loaded '
                    + str(len(st.session_state.data['matches']))
                    + ' matches.')
    ## Initialize st.session_state.data
    if 'data' not in st.session_state:
        st.session_state.data = {}

    ## Create JSON FILE
    if 'leagueId' in st.session_state.data:
        if st.button('Write json'):
            with open('summoners_test.json', 'w') as outfile:
                json.dump(st.session_state.data, outfile)
#################################################
    ## For testing, load json file
    ## REMOVE THIS
    data = {}
    if st.button('Load json'):
        with open('summoners_test.json') as f:
            data = json.load(f)
            st.session_state.data = data
        st.session_state.submitted = True
#################################################
    ## Show desired data
    if st.session_state.submitted:
        data_options = [
            'Winning Units',
            'Losing Units',
            'First Place Units',
            'Eighth Place Units',
            'Machine Learning'
            ]
        select = st.selectbox('Select what data to show', data_options)
        if select in data_options[:4]:
            n_units = st.number_input(
                'How many units',
                key='unit_count',
                min_value=1,
                max_value=10,
                value=3)
        raw_data = st.checkbox('Show raw data', key='raw_data')
        show_data = st.button('Show Data')
        if show_data:
            data = st.session_state.data
            ## Winning Units
            if select == data_options[0]:
                df = get_units_data(data,False)
                units = score_units(df)
                st.write(
                'These are the top ' +
                str(n_units) +
                ' winning units from the last ' +
                str(count) +
                ' games:')
                st.write(units[:n_units][['score']])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units)
            ## Losing Units
            elif select == data_options[1]:
                df = get_units_data(data,False)
                units = score_units(df)
                st.write(
                    'These are the worst ' +
                    str(n_units) +
                    ' losing units from the last ' +
                    str(count) +
                    ' games:')
                st.write(units.sort_values(by='score')[:n_units][['score']])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units.sort_values(by='score', ascending=True))
            ## First Place Units
            elif select == data_options[2]:
                df = get_units_data(data,False)
                units = score_units(df)
                if 1 not in units.columns.tolist():
                    error = 'ERROR: no units got first place in this search'
                    return st.write(error)
                st.write(
                    'These are the ' +
                    str(n_units) +
                    ' units that placed first most often in the last ' +
                    str(count) +
                    ' games:')
                st.write(units.sort_values(by=1, ascending=False)[:n_units][[1]])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units)
            ## Eighth Place Units
            elif select == data_options[3]:
                df = get_units_data(data,False)
                units = score_units(df)
                if 8 not in units.columns.tolist():
                    error = 'ERROR: no units got eighth place in this search'
                    return st.write(error)
                st.write(
                    'These are the ' +
                    str(n_units) +
                    ' units that placed eighth most often in the last ' +
                    str(count) +
                    ' games:')
                st.write(units.sort_values(by=8, ascending=False)[:n_units][[8]])
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id', 'placement']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df.drop(['e', 'name'], axis=1))
                    st.write('Placements by All Units: ')
                    st.write(units.sort_values(by='score', ascending=True))
                    st.write(units)
            ## Machine Learning Prep
            elif select == data_options[4]:
                data=st.session_state.data
                df = collect_units_items(data)
                if "df" not in st.session_state:
                    st.session_state.df = df
                # grouped = df.groupby(['character_id', 'placement', 'match_id']).sum()
                # for col in grouped.columns:
                #     grouped.loc['max', col] = df[col].astype(float).max()
                # st.write(grouped.shape)
                df['target'] = (df['placement']<=4)
                st.write(df)
                if raw_data:
                    st.write('Raw Data:')
                    cols = df.columns.tolist()
                    cols = [x for x in cols if x not in ['character_id']]
                    cols = ['character_id'] + cols
                    df = df[cols]
                    st.write(df)
                ml_model_time()

# def ml_model_time():
#
#
#         if st.button('quick show'):
#             st.write('nothing to show')
########################################################################
########################################################################
########################################################################
if __name__ == '__main__':
    main()
