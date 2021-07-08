## Functions python file to import to streamlit python file

import pandas as pd
import streamlit as st
import riotwatcher

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
    return df

## For data options 1:5: Units data
def get_units_data(data, only, watcher):
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
            participant = findParticipant(data['matches'][id], data['puuid'])
            temp_df = pd.json_normalize(participant['units'])
            temp_df['summoner'] = data['summoner']
            temp_df['placement'] = participant['placement']
            temp_df['match_id'] = id
            df = df.append(temp_df)
    ## Interested in all summoners
        elif only == False:
            for j in range(8):
                participant = data['matches'][id]['info']['participants'][j]
                temp_df = pd.json_normalize(participant['units'])
                temp_df['puuid'] = participant['puuid']
                temp_df['placement'] = participant['placement']
                temp_df['match_id'] = id
                for puuid in temp_df['puuid']:
                    sum = watcher.summoner.by_puuid('na1',puuid)['name']
                    temp_df.loc[temp_df['puuid']==puuid,'summoner']=sum
                df = df.append(temp_df)
                df = df.drop('puuid', axis=1)
    ## Counter column
    df['e'] = 1
    return df

def get_desired_units(data, count=3, how='win'):
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
    group_by = group_by.fillna(0)
    undefeated = []

    if (any(x in [1,2,3,4] for x in (group_by.columns))==False) and (how=='win'):
        raise ValueError('There are no wins in this dataset')
    elif (any(x in [5,6,7,8] for x in (group_by.columns))==False) and (how=='lose'):
        raise ValueError('There are no losses in this dataset')

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

        ## Get undefeated units    and assign score to win score to avoid divide-by-zero error
        if lose_score == 0:
            undefeated.append(unit)
            score = win_score
        else:
            score = win_score/lose_score
        group_by.loc[unit,'score'] = score

    ## Print undefeated units
    if len(undefeated) != 0:
        st.write('These units did not lose a game:', undefeated)

    ## Filter accordingly
    if how == 'win':
        units = group_by.sort_values(by='score', ascending=False)[:count]
        return units[['score']]
    elif how == 'first':
        units = group_by[group_by[1] == group_by[1].max()]
        return units[[1]]
    elif how == 'lose':
        units = group_by.sort_values(by='score', ascending=True)[:count]
        return units[['score']]
    elif how == 'eighth':
        units = group_by.loc[group_by[8] == group_by[8].max()]
        return units[[8]]

def findParticipant(match, puuid):
    '''
    function to find specific participant by puuid in a single match
    used in other function calls

    '''
    for i in range(8):
        participant = match['info']['participants'][i]
        if puuid == participant['puuid']:
            return participant
