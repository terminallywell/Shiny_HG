'''Packages and shared functions'''

from shiny import App, render, reactive, ui
from pyHG import *


def to_tableau(input_file) -> pd.DataFrame:
    '''
    Function to convert Shiny input file into DataFrame
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
    Function to turn the regular solution output into nice text
    '''
    names = get_constraint_names(data)

    text = f'{len(solutions)} solution{"" if len(solutions) == 1 else "s"} found:\n'

    for i, solution in enumerate(solutions): 
        solution_output = f'\n[Solution {i + 1}]\n'
        for name, weight in zip(names, solution):
            solution_output += f'{name}: {int(weight)}\n'
        text += solution_output
    
    return text


# Work in progress
def weights_and_harmonies(tableau: pd.DataFrame, solution: list[float]) -> pd.DataFrame:
    '''
    Returns a copy of tableau with weights added to constraint column names as well as a Harmony column
    '''
    new_tableau = tableau.rename(
        columns={const_name: const_name + f' ({int(weight)})' for const_name, weight in zip(get_constraint_names(tableau), solution)}
    )

    if 'HR' in new_tableau.columns:
        rows = new_tableau.iloc[:, 4:].iterrows()
    else:
        rows = new_tableau.iloc[:, 3:].iterrows()

    new_tableau['H'] = [sum(-viol * weight for viol, weight in zip(row[1], solution)) for row in rows]

    return new_tableau
