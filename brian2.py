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
- Switch some reactive.Values (e.g. sol_text) into reactive.calc()
'''

from common import *


app_ui = ui.page_sidebar(

    # input portion (sidebar)
    ui.sidebar(
        ui.navset_underline(
            ui.nav_panel(
                'Build/Edit Tableau',
                ui.output_ui('select_winner'), # provisional
                ui.download_button('save', 'Save as CSV') # in development
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
    data = reactive.Value(pd.DataFrame()) # tableau data
    solutions = reactive.Value(list()) # list of solutions
    sol_text = reactive.Value(str()) # solution text

    # Reset reactive values every time new file is uploaded
    @reactive.effect
    def resetter():
        solutions.set([])
        sol_text.set('')
        if input['file'](): # suppress error until file uploaded
            # read in file and convert to tableau
            data.set(to_tableau(input['file']()))
    
    # Tableau solver
    @reactive.effect
    @reactive.event(input['solve'])
    def _():
        if input['file']():
            solutions.set(solve_language(data()))
            sol_text.set(solution_simple(data(), solutions()))
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
            if solutions(): # tableau is solved ...
                tableau = apply_solution( # ... display tableau with weights and harmony
                    data(),
                    solutions()[int(input['sol_index']()[-1]) - 1] # solution selected in select_solution
                )
            else:
                tableau = data() # otherwise display without weights and harmony
            
            return tidy_tableaux(tableau)

    # Winner selection render function (provisional)
    @render.ui
    def select_winner():
        if input['file']():
            selects = []
            for ur in gen_URlist(data()):
                selects.append(
                    ui.input_selectize(
                        f'winner_{ur}',
                        f'Select winner for {ur}',
                        gen_SR(data(), ur),
                        selected=get_winner(data(), ur),
                    )
                )

            return selects
    
    # Update tableau based on selected winner
    @reactive.effect
    def update_tableau():
        if input['file']():
            with reactive.isolate(): # prevents data() access and modification from causing infinite loop 
                new_data = data().copy()
            
            for ur in gen_URlist(new_data):
                change_winner(new_data, ur, input[f'winner_{ur}']())

            data.set(new_data)

            # reset solutions
            solutions.set([])
            sol_text.set('')

    # Download current tableau
    @session.download(filename='tableau.csv')
    def save():
        # under development
        ...


app = App(app_ui, server)
