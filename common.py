'''Packages and shared functions'''

from shiny import App, render, reactive, ui
from pyHG import *

nan = float('nan')

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

# DEPRECATED
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


def solution_text(solutions: list[list[float]]) -> str:
    num = len(solutions)
    if num == 0:
        return 'No solution found!'
    return f'{num} solution{"" if num == 1 else "s"} found.\n'


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

    new_data['H'] = [sum(-viol * weight for viol, weight in zip(row, solution)) for index, row in rows]

    return new_data


def get_winner(data: pd.DataFrame, ur: str) -> str | None:
    '''
    Returns the winning SR of the given UR.
    '''
    try:
        return data.loc[(data['UR'] == ur) & (data['Obs'] == 1), 'SR'].to_list()[0]
    except IndexError:
        pass


def viols(data: pd.DataFrame, cName: str, cand: str) -> int:
    '''Modified `Con()` function in pyHG.'''
    colname = 'HR' if 'HR' in data.columns else 'SR'
    try:
        return int(data.loc[data[colname]==cand, cName].values[0])
    except (KeyError, IndexError):
        return 0

# DEPRECATED
def change_winner(data: pd.DataFrame, ur: str, winner: str) -> None:
    '''
    Changes the winning SR of the given UR in the tableau.
    '''
    mask = (data['SR'] == winner) & (~data['SR'].duplicated(keep='first'))
    data.loc[(data['UR'] == ur) & mask, 'Obs'] = 1
    data.loc[(data['UR'] == ur) & ~mask, 'Obs'] = nan


def render_ui(tag, id, *args, **kwargs):
    '''
    Attaches a dynamic UI element to another.
    
    Basically, you can use `add_ui(tag, ui_id)` in place of `def ui_id(): return tag`,
    and `ui.p(id=ui_id)` (or any element with an id parameter) in place of `ui.output_ui(ui_id)`.
    
    ### Parameters
    * `tag` The UI element to be attached.
    * `id` The ID of the UI element to attach your UI element to.
    '''
    div = str(hash(id))
    ui.remove_ui('#' + div)
    ui.insert_ui(ui.div(tag, id=div), '#' + id, *args, **kwargs)


def tableau_to_csv(data: pd.DataFrame, *args, **kwargs) -> None:
    '''
    Formats tableau as CSV. (TODO: In development)
    '''


# DEPRECATED
def tableau_to_dict(tableau: pd.DataFrame) -> tuple[dict, dict]:
    '''
    Converts `DataFrame` tableau into `dict` data used in `build_tableau()`.
    '''
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
    winner = {}
    for index, row in tableau.iterrows():
        if 'HR' in tableau:
            for c in row.keys()[4:]:
                data[row['UR']][row['SR']][row['HR']][c] = row[c]
        else:
            for c in row.keys()[3:]:
                data[row['UR']][row['SR']][c] = row[c] # type: ignore
        
        if row['Obs'] == 1:
            winner[row['UR']] = row['SR']
    
    return data, winner

# DEPRECATED
def build_tableau(data: dict, winner: dict, hidden: bool = True) -> pd.DataFrame:
    '''
    TODO: docstring
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
                    if sr == winner[ur] and not obs_added:
                        obs.append(1)
                        obs_added = True
                    else:
                        obs.append(nan)
                    hrs.append(hr)
                    for c in data[ur][sr][hr]:
                        consts.setdefault(c, []).append(data[ur][sr][hr][c])
            else:
                urs.append(ur)
                srs.append(sr)
                obs.append(1 if sr == winner[ur] else nan)
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
