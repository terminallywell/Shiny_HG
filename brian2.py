'''
## Brian's main application (edit tableau in development)

### Current features
- Uploading tableau CSV files and solving
- Selecting and integrating solution into tableau with Harmony column

### Work in progress
- Editing uploaded tableau in "Build/Edit Tableau" tab
    - Only winner selection is implemented currently
- Saving modified tableau as CSV

### Possible improvements
- Switch some reactive.Values (e.g. sol_text) into reactive.calc (for simplification) <- I forgot what this was about
- Hide solution selection UI if no HR (always gonna be 0 or 1 solution)
- Display "Solving..." text while solving
'''

from common import *


app_ui = ui.page_sidebar(

    # input portion (sidebar)
    ui.sidebar(
        ui.navset_underline(
            ui.nav_panel(
                'Build/Edit Tableau',
                ui.output_ui('select_winner'), # provisional
                # ui.download_button('save', 'Save as CSV'), # in development
            ),
            ui.nav_panel(
                'Upload CSV',
                ui.input_file('file', 'Upload tableau'),
            ),
            selected='Upload CSV', # to be deleted once build tableau feature is completed
        ),
        open='always',
        width=350,
    ),

    # output portion (main)
    ui.input_action_button('solve', 'Solve', width='150px', class_='btn-primary'),
    ui.output_text('solve_result'),
    ui.output_ui('select_solution'),
    ui.output_data_frame('render_tableau'),
)


def server(input, output, session):
    data = reactive.Value(dict())
    winner = reactive.Value(dict())
    tableau = reactive.Value(pd.DataFrame())
    hidden = reactive.Value(bool())
    solutions = reactive.Value(list())
    sol_text = reactive.Value(str())

    # Convert CSV to to dict
    @reactive.effect
    def upload():
        if input['file'](): # suppress error until file uploaded
            # read in file and convert
            tab = to_tableau(input['file']())
            hidden.set('HR' in tab)

            d, w = tableau_to_dict(tab)
            data.set(d)
            winner.set(w)
    
    # Convert dict to tableau
    @reactive.effect
    def update_tableau():
        if input['file']():
            tableau.set(build_tableau(data(), winner(), hidden()))

    # Reset solutions every time data is uploaded or modified
    @reactive.effect
    def reset_():
        triggers = data(), winner()

        solutions.set([])
        sol_text.set('')
    
    # Tableau solver
    @reactive.effect
    @reactive.event(input['solve'])
    def _():
        if input['file']():
            solutions.set(solve_language(tableau()))
            sol_text.set(solution_text(solutions()))
        else:
            ui.modal_show(ui.modal('No tableau found.'))

    # Display result
    @render.text
    def solve_result():
        return sol_text()
    
    # Select solution to apply
    @render.ui
    def select_solution():
        if solutions(): # show only if tableau is solved (i.e. at least one solution is found)
            return ui.input_selectize(
                'sol_index',
                'Select solution to apply:',
                [*map(lambda i: f'Solution {i + 1}', range(len(solutions())))]
            )

    # Tableau render function
    @render.data_frame
    def render_tableau():
        if input['file']():
            if solutions(): # if language is solved ...
                t = apply_solution( # ... display tableau with weights and harmony
                    tableau(),
                    solutions()[int(input['sol_index']()[-1]) - 1] # solution selected in select_solution
                )
            else:
                t = tableau() # otherwise display without weights and harmony
            
            return tidy_tableaux(t)

    # Winner selection render function (provisional)
    @render.ui
    def select_winner():
        if input['file']():
            selects = []
            for ur in gen_URlist(tableau()):
                selects.append(
                    ui.input_selectize(
                        f'winner_{ur}',
                        f'Select winner for {ur}',
                        gen_SR(tableau(), ur),
                        selected=get_winner(tableau(), ur),
                    )
                )

            return selects
    
    # Update winners based on selection
    @reactive.effect
    def update_winner():
        winner.set({ur: input[f'winner_{ur}']() for ur in data()})

    # Download current tableau
    @session.download(filename='tableau.csv')
    def save():
        # under development
        ...


app = App(app_ui, server)
