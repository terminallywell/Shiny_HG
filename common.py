'''Packages and shared functions'''

from shiny import App, render, reactive, ui
from pyHG import *


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
    ListOfConNames = get_constraint_names(data)

    solution_text = f'{len(solutions)} solution{"" if len(solutions) == 1 else "s"} found\n'

    for solution in solutions: 
        solution_output = '-----------------------------\n'
        for constraint_name, constraint_weight in zip(ListOfConNames, solution):
            solution_output += f'{constraint_name}: {int(constraint_weight)}\n'
        solution_text += solution_output
    
    return solution_text


# Work in progress
def weights_and_harmonies(tableau: pd.DataFrame, weights: list[int]) -> pd.DataFrame:
    '''
    Adds weights to constraint column names, as well as adds a Harmony column
    '''
    new_tableau = tableau.rename(
        columns={const_name: const_name + f' ({int(weight)})' for const_name, weight in zip(get_constraint_names(tableau), weights)}
    )

    if 'HR' in new_tableau.columns:
        rows = new_tableau.iloc[:, 4:].iterrows()
    else:
        rows = new_tableau.iloc[:, 3:].iterrows()

    new_tableau['H'] = [sum(viol * weight for viol, weight in zip(row[1], weights)) for row in rows]

    return new_tableau
