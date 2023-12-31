'''Packages and shared functions'''

from shiny import App, render, reactive, ui
from pyHG import *

# For debugging only
import sys, datetime, time

def eprint(*args, **kwargs): print(*args, file=sys.stderr, flush=True, **kwargs)

def to_tableau(input_file) -> pd.DataFrame:
    '''
    Converts Shiny input file into DataFrame.
    '''
    return read_file(input_file[0]["datapath"][:-4])


def ss(input: str, sep: str = ',') -> list[str]:
    '''
    Splits and Strips the input, ignoring empty substrings.

    ### Parameters
    * `input: str` The input string to be split and stripped.
    * `sep: str` The separator used to split the string. Default: `,`

    ### Example
    >>> ss('this, is , an, example  , ,,') 
    ['this', 'is', 'an', 'example']
    '''
    return [item.strip() for item in input.split(sep) if item.strip()]


def create_solution_table(data: pd.DataFrame, solutions: list[list[float]]) -> str:
    '''
    Solution list pretty-formatter.
    '''
    if len(solutions) == 0:
        return 'No solution found!'
    
    names = get_constraint_names(data)

    text = f'{len(solutions)} solution{"" if len(solutions) == 1 else "s"} found:\n'

    for i, solution in enumerate(solutions): 
        text += f'\n[Solution {i + 1}]\n'
        for name, weight in zip(names, solution):
            text += f'{name}: {int(weight)}\n'
    
    return text


def solution_simple(data: pd.DataFrame, solutions: list[list[float]]) -> str:
    if len(solutions) == 0:
        return 'No solution found!'
    return f'{len(solutions)} solution{"" if len(solutions) == 1 else "s"} found.\n'


def apply_solution(data: pd.DataFrame, solution: list[float]) -> pd.DataFrame:
    '''
    Returns a copy of tableau with weights added to constraint column names as well as a Harmony column.
    '''
    new_data = data.rename(
        columns={const_name: const_name + f' : {int(weight)}' for const_name, weight in zip(get_constraint_names(data), solution)}
    )

    if 'HR' in new_data.columns:
        rows = new_data.iloc[:, 4:].iterrows()
    else:
        rows = new_data.iloc[:, 3:].iterrows()

    new_data['H'] = [sum(-viol * weight for viol, weight in zip(row[1], solution)) for row in rows]

    return new_data


def get_winner(data: pd.DataFrame, ur: str) -> str:
    '''
    Returns the winning SR of the given UR.
    '''
    return data.loc[(data['UR'] == ur) & (data['Obs'] == 1), 'SR'].to_list()[0]


def change_winner(data: pd.DataFrame, ur: str, winner: str) -> None:
    '''
    Changes the winning SR of the given UR in the tableau.
    '''
    mask = (data['SR'] == winner) & (~data['SR'].duplicated(keep='first'))
    data.loc[(data['UR'] == ur) & mask, 'Obs'] = 1
    data.loc[(data['UR'] == ur) & ~mask, 'Obs'] = np.NaN


def tableau_to_csv(data: pd.DataFrame, *args, **kwargs) -> None:
    '''
    Formats tableau as CSV. (In development)
    '''


def build_tableau(data: dict, winner: dict, hidden: bool = True) -> pd.DataFrame:
    '''
    data: {UR: {SR: {HR: {Const: int}}}} or {UR: {SR: {Const: int}}} dictionary
    winner: {UR: SR} dictionary
    '''
    urs = []
    srs = []
    obs = []
    hrs = []
    consts = {}

    for ur in data:
        for sr in data[ur]:
            if hidden:
                obs_added = False
                for hr in data[ur][sr]:
                    urs.append(ur)
                    srs.append(sr)
                    if sr == winner[ur] and not obs_added :
                        obs.append(1)
                        obs_added = True
                    else:
                        obs.append(np.nan)
                    hrs.append(hr)
                    for c in data[ur][sr][hr]:
                        consts.setdefault(c, []).append(data[ur][sr][hr][c])
            else:
                urs.append(ur)
                srs.append(sr)
                obs.append(1 if sr == winner[ur] else np.nan)
                for c in data[ur][sr]:
                    consts.setdefault(c, []).append(data[ur][sr][c])
    
    tableau = pd.DataFrame()
    tableau['UR'] = urs
    tableau['SR'] = srs
    tableau['Obs'] = obs
    if hidden:
        tableau['HR'] = hrs
    for c in consts:
        tableau[c] = consts[c]

    return tableau

# Example data
data_withHR = {
    'bada': { # UR layer
        'bada': { # SR layer
            'bAda': { # HR layer
                'c1': 1, # Constraints layer
                'c2': 0,
                'c3': 1,
            },
            'badA': {
                'c1': 0,
                'c2': 0,
                'c3': 1,
            },
        },
        'pata': {
            'pAta': {
                'c1': 1,
                'c2': 0,
                'c3': 0,
            },
            'patA': {
                'c1': 0,
                'c2': 1,
                'c3': 0,
            },
        }
    },
    'lolo': {
        'lolo': {
            'lOlo': {
                'c1': 1,
                'c2': 0,
                'c3': 1,
            },
            'lolO': {
                'c1': 0,
                'c2': 0,
                'c3': 1,
            },
        },
        'roro': {
            'rOro': {
                'c1': 1,
                'c2': 0,
                'c3': 0,
            },
            'rorO': {
                'c1': 0,
                'c2': 1,
                'c3': 0,
            },
        }
    }
}
