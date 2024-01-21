'''Packages and shared functions'''

from shiny import App, render, reactive, ui, module, req
from pyHG import *
import shinyswatch

nan = float('nan')

# For debugging only
import sys, datetime, time
def eprint(*args, **kwargs): print(*args, file=sys.stderr, flush=True, **kwargs)


def to_tableau(input_file) -> pd.DataFrame:
    '''Converts Shiny input file into DataFrame.'''
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


def render_ui(tag, id, *args, **kwargs):
    '''
    Attaches a dynamic UI element to another.
    
    Instead of writing:
    ```
    @render.ui
    def ui_id():
        return tag
    ```
    you can do:
    ```
    @reactive.effect
    def _():
        render_ui(tag, 'ui_id')
    ```
    
    ### Parameters
    * `tag` The UI element to be attached.
    * `id` The ID of the UI element (usually `ui.output_ui()`) to attach/insert your UI element to.
    '''
    eprint('render_ui called')
    ui.remove_ui('#div_' + id)
    ui.insert_ui(ui.div(tag, id='div_' + id), '#' + id, *args, **kwargs)


def solution_text(solutions: list[list[float]]) -> str:
    num = len(solutions)
    if num == 0:
        return 'No solution found!'
    return f'{num} solution{"" if num == 1 else "s"} found.\n'


def apply_solution(tableau: pd.DataFrame, solution: list[float]) -> pd.DataFrame:
    '''Returns a copy of tableau with weights added to constraint column names as well as a Harmony column.'''
    new_tableau = tableau.rename(
        columns={const_name: const_name + f' : {int(weight)}' for const_name, weight in zip(get_constraint_names(tableau), solution)}
    )

    if 'HR' in new_tableau.columns:
        rows = new_tableau.iloc[:, 4:].iterrows()
    else:
        rows = new_tableau.iloc[:, 3:].iterrows()

    new_tableau['H'] = [sum(-viol * weight for viol, weight in zip(row, solution)) for index, row in rows]

    return new_tableau


def get_winner(tableau: pd.DataFrame, ur: str) -> str | None:
    '''Returns the winning SR of the given UR.'''
    try:
        return tableau.loc[(tableau['UR'] == ur) & (tableau['Obs'] == 1), 'SR'].values[0]
    except IndexError:
        pass


def get_viols(tableau: pd.DataFrame, c: str, ur: str, sr: str, hr: str | None = None) -> int:
    '''
    Modified version pyHG's `Con()` function with:
    - Taylored error handling
    - Addressing duplicate SR/HR cases
    '''
    try:
        return int(tableau.loc[(tableau['UR'] == ur) & (tableau['SR'] == sr) & (tableau['HR'] == hr if hr else True), c].values[0])
    except (KeyError, IndexError):
        return 0


def get_HRs(tableau: pd.DataFrame, ur: str, sr: str) -> list[str]:
    '''Modified version of pyHG's `gen_HR()` function, addressing duplicate SR cases (different URs, same SR).'''
    return tableau.loc[(tableau['UR'] == ur) & (tableau['SR'] == sr), 'HR'].tolist()


def tableau_to_csv(tableau: pd.DataFrame, *args, **kwargs) -> None:
    '''Formats tableau as CSV. (TODO: In development)'''
