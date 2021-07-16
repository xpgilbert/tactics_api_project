## Functions python file to import to streamlit python file

import pandas as pd
import streamlit as st
import riotwatcher
import json
from sklearn.preprocessing import MultiLabelBinarizer

## For data option 0: End of match data
def get_endings_dataframe(data, only):
    '''
    Build dataframe of end of match data for further analysis.

    Parameters
    ----------
    data : dict
        dictionary of data pulled from initialized form
    only : bool, optional
        if only interested in the named summoner

    Returns
    -------
    df : pandas dataframe
        The endings dataframe
    '''
    df = pd.DataFrame()
    for i in range(len(data['match_ids'])):
        id = data['match_ids'][i]
        end_data = pd.json_normalize(data['matches'][id]['info']['participants'])
        end_data.drop(
                [
                'traits',
                'units',
                'companion.content_ID',
                'companion.skin_ID',
                'companion.species'
            ], axis=1, inplace=True)
        df = df.append(end_data)
        i +=1
    ## Check if only interested in requested summoner
    if only == True:
        df = df[df['puuid']==data['puuid']]
    return df
def get_units_data(data, only):
    '''
    Build dataframe of unit data for further analysis.
    Adds "e" counter column for groupby in get_units function

    Parameters
    ----------
    data : dict
        dictionary of data pulled from initialized form
    only : bool
        if only interested in the named summoner
    watcher : riotwatcher class, optional
        only required if only = False.  used to pull summoner names
    Returns
    -------
    df : pandas dataframe
        The units dataframe
    '''
    df = pd.DataFrame()
    for i in range(len(data['match_ids'])):
        id = data['match_ids'][i]
    ## Only interested in named summoner
        if only == True:
            participant = find_participant(data['matches'][id], data['puuid'])
            temp_df = pd.json_normalize(participant['units'])
            temp_df['placement'] = participant['placement']
            temp_df['match_id'] = id
            df = df.append(temp_df)
    ## Interested in all summoners
        elif only == False:
            for j in range(8):
                participant = data['matches'][id]['info']['participants'][j]
                temp_df = pd.json_normalize(participant['units'])
                temp_df['placement'] = participant['placement']
                temp_df['match_id'] = id
                df = df.append(temp_df)
    ## Counter column
    df['e'] = 1
    return df
def score_units(data):
    '''
    Get the units by desired filter method and return dataframe with
    appropriate column for comparison.

    Parameters
    ----------
    data : pandas dataframe
        dataframe from getUnitsDataFrame()
    how : str, optional
        Which units to return.
        'win' returns top4,
        'first' returns first place only,
        'lose' reutnrs bot4,
        'eighth' returns eighth place only.
        The default is 'win'.
    count : int, optional
        Number of units to return. The default is 3.

    Returns
    -------
    units : pandas dataframe
        The units by the desired filter and the corresponding score if
        how is win/lose, or placement count if first/eigth

    '''
    ## Group by unit and placement
    group_by=data.groupby(['character_id','placement']).count()['e'].unstack()
    group_by=group_by.fillna(0)
    undefeated=[]
    ##if (any(x in [1,2,3,4] for x in (group_by.columns))==False) and (how=='win'):
    ##    raise ValueError('There are no wins in this dataset')
    ##elif (any(x in [5,6,7,8] for x in (group_by.columns))==False) and (how=='lose'):
    ##    raise ValueError('There are no losses in this dataset')
    ## Filter columns
    win_cols = [col for col in group_by.columns if col <=4]
    lose_cols = [col for col in group_by.columns if col > 4]
    ## Build weights based on available placements
    for unit in list(group_by.index):
        weights = []
        for i in win_cols:
            if i == 1:
                weights.append(4)
            elif i == 2:
                weights.append(3)
            elif i == 3:
                weights.append(2)
            elif i == 4:
                weights.append(1)
        win_score =(group_by.loc[unit, win_cols]*weights).sum()
        weights = []
        for i in lose_cols:
            if i == 5:
                weights.append(1)
            elif i == 6:
                weights.append(2)
            elif i == 7:
                weights.append(3)
            elif i == 8:
                weights.append(4)
        lose_score=(group_by.loc[unit, lose_cols]*weights).sum()
        ## Get undefeated units and assign score to win
        ## score to avoid divide-by-zero error
        if lose_score == 0:
            undefeated.append(unit)
            score = win_score
        else:
            score = win_score/lose_score
        group_by.loc[unit,'score'] = score
    units = group_by.sort_values(by='score', ascending=False)
    units['num_games'] = units[list(group_by.columns[:-1])].sum(axis=1)
    ## Print undefeated units
    if len(undefeated) != 0:
        st.write('These units did not lose a game:', undefeated)
    return units
def load_summoner_data(region, name, count, watcher):
    '''
    Requests the data from Riot API using riotwatcher and creates a
    dictionary of the relevant id information and match data to be used
    as input to the custom functions throughout the app.

    Parameters
    ----------
    region : str
        summoner region to query
    name : str
        if only interested in the named summoner
    count : int
        number of matches to return
    watcher : riotwatcher class, optional
        watcher class from riotwatcher to interface Riot API
    Returns
    -------
    data : dict
        Dictionary of relevant data.
        Key:Value pairs are:
        puuid: player globally unique id
        summoner: summoner name
        region: summoner region
        match_ids: list of match ids
        matches: dictionary of match data with match_ids as keys
    '''
    ## Some Riot API needs platform, not region
    if region == 'na1':
        platform = 'americas'
    ## Find puuid for named summoner
    puuid = watcher.summoner.by_name(region, name)['puuid']
    ## Get count sized match ids list
    match_ids = watcher.match.by_puuid(platform, puuid, count)
    ## Loop over match_ids to pull match data
    matches = {}
    for i in range(len(match_ids)):
        if i % 2 == 0:
            st.write(i)
        matches[match_ids[i]]=watcher.match.by_id(platform,match_ids[i])
    ## Create dictionary to return
    data = {
    'puuid':puuid,
    'summoner':name,
    'region':region,
    'match_ids':match_ids,
    'matches':matches
    }
    return data
def load_league_data(region, queue, name, count, watcher):
    '''
    Requests the data from Riot API using riotwatcher and creates a
    dictionary of the relevant id information and league data to be used
    as input to the custom functions throughout the app.

    Parameters
    ----------
    region : str
        summoner region to query
    queue : str
        which game mode to query, either Ranked or Hyper Roll.
    name : str
        if only interested in the named summoner
    count : int
        number of matches per summoner to return
    watcher : riotwatcher class, optional
        watcher class from riotwatcher to interface Riot API
    Returns
    -------
    data : dict
        Dictionary of relevant data.
        Key:Value pairs are:
        leagueId: unique league id
        region: summoner region
        summoner_id: summoner id originally queued against
        match_ids: list of unique match ids
        matches: dictionary of unique match data with match_ids as keys
    '''
    ## Get encrypted summoner_id
    sum_id = watcher.summoner.by_name(region, name)['id']
    ## Get desired queue and coresponding league_id
    for league in watcher.league.by_summoner(region, sum_id):
        if league['queueType'] == queue:
            league_id = league['leagueId']
    ## Get League API data
    league_data = watcher.league.by_id(region, league_id)
    league_name = league_data['name']
    league_tier = league_data['tier']
    ## Get all summoner ids from league
    sum_ids = []
    for entry in league_data['entries'][:10]:
        sum_ids.append(entry['summonerId'])
    ## Get all matches per summoner
    summoners = {}
    for id in sum_ids:
        puuid = watcher.summoner.by_id(region, id)['puuid']
        match_ids = watcher.match.by_puuid('americas', puuid, count)
        sum_matches = {}
        for i in range(len(match_ids)):
            id = match_ids[i]
            temp_match = watcher.match.by_id('americas', id)
            sum_matches[id] = temp_match
        summoners[puuid] = sum_matches
    ## Find all unique matches:
    unique_ids = []
    unique_matches = {}
    for summoner in summoners.values():
        for match in summoner.values():
            match_id = match['metadata']['match_id']
            if match_id not in unique_ids:
                unique_ids.append(match_id)
                unique_matches[match_id] = match
    data = {
        'leagueId':league_id,
        'name':league_name,
        'tier':league_tier,
        'region':region,
        'queue':queue,
        'summoner_id':sum_id,
        'match_ids':unique_ids,
        'matches':unique_matches
    }
    return data
def get_items_data(df):
    '''
    Creates a boolean dataframe with information on items used by each
    unit in each match.  Links to the static data which must be stored
    in a folder called 'set5'. This must be renamed from 'set5patchXXXX'
    and lives in the same directory as this functions.py file.

    Parameters
    ----------
    df : pandas DataFrame
        dataframe from get_units_data(dict, only = False)
    Returns
    -------
    data : pandas DataFrame
        boolean dataframe of
    '''
    ## Get unique item lists, coded
    unique_items = df.explode('items')['items'].unique()
    ## Save character_id index for joining later
    unit_index = df['character_id']
    mlb = MultiLabelBinarizer(classes=unique_items)
    mlb_object = mlb.fit_transform(df.set_index('character_id')['items'])
    mlb_columns = pd.DataFrame(mlb.classes_).transpose().to_dict('records')[0]
    item_frame = pd.DataFrame(mlb_object).rename(columns=mlb_columns)
    #item_bools = boolean_df(df.set_index('character_id')['items'], unique_items)
    ## Get corresponding item names from static data
    with open('set5/items.json', 'r') as f:
        static_items = json.load(f)
    item_dict = {float('nan'):'no_items'}
    for item in static_items:
        item_dict[item['id']] = item['name']
    ## Rename columns
    item_frame = item_frame.rename(columns=item_dict).set_index(unit_index)
    ## Attach match id and placement for joining later
    #df = item_frame.join(df.set_index('character_id')[['match_id','placement']])
    df = item_frame
    return df
def collect_units_items(data):
    '''
    Get a large dataframe for modeling.  Mix of continuous and binary
    variables, including dummy variables from pandas.
    Parameters
    ----------
    data : dict
        Dictionary loaded from st.session_state.data
    Returns
    -------
    df : pandas dataframe
        Every unit and their items as dummies for every match in dataset
    '''
    ## Get units dataframe from data
    units = get_units_data(data, False)
    ## Get items dataframe from data
    items = get_items_data(units)
    ## Remove unecessary columns and reset indeces
    units = units.drop(['items', 'name', 'e'], axis=1)
    units.reset_index(drop=True, inplace=True)
    items.reset_index(drop=True, inplace=True)
    ## Get placement dummies
    placement_dummies = pd.get_dummies(units['placement'])
    ## Concat all the frames
    df = pd.concat([units, placement_dummies, items], axis=1)
    return df
def get_api_key():
    f = open('../apikey.txt', 'r')
    return f.read()
def find_participant(match, puuid):
    '''
    function to find specific participant by puuid in a single match
    used in other function calls
    '''
    for i in range(8):
        participant = match['info']['participants'][i]
        if puuid == participant['puuid']:
            return participant
