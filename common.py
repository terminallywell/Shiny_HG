'''Packages and shared functions'''

from shiny import App, render, reactive, ui
from pyHG import *


def ss(input: str, sep: str = ',') -> list[str]:
    '''
    Splits and Strips the input.

    ### Parameters
    * `input: str` The input string to be split and stripped.
    * `sep: str` The separator used to split the string. Default: `,`

    ### Example
    >>> ss('this, is , an, example  ')
    ['this', 'is', 'an', 'example']
    '''
    return [item.strip() for item in input.split(sep) if len(item.strip()) > 0]


# provisional
def solutions_pretty(const_names: list[str], solutions: list[list[int]]) -> str:
    '''Solution pretty-formatter'''
    out = f'{len(solutions)} solution{"" if len(solutions) == 1 else "s"} found:\n'
    for solution in solutions:
        sol = '--------------------\n'
        for name, weight in zip(const_names, solution):
            sol += f'{name}: {int(weight)}\n'
        out += sol

    return out


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
