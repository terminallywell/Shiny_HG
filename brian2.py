'''Brian's main application v2'''

from common import *


app_ui = ui.page_sidebar(

    # input portion (sidebar)
    ui.sidebar(
        ui.navset_underline(
            ui.nav(
                'Build/Edit Tableau',
                'coming soon (maybe we can start small from violation count editing)'
            ),
            ui.nav(
                'Upload CSV',
                ui.input_file('file', 'Upload tableau'),
                ui.output_text_verbatim('solution_text'),
            ),
            selected='Upload CSV', # to be deleted
        ),
        open='always',
        width=350,
    ),

    # output portion (main)
    ui.input_action_button('solve', 'Solve', width='150px', class_='btn-primary'),
    ui.output_ui('select_solution'),
    ui.output_data_frame('render_tableau'),
)


def server(input, output, session):
    data = reactive.Value() # tableau data
    solutions = reactive.Value() # list of solutions
    sol_text = reactive.Value() # solution text

    @reactive.Effect
    def _():
        # clear solutions and text every time file is uploaded
        solutions.set([])
        sol_text.set('Solutions will be displayed here')
        if input['file'](): # suppress error until file uploaded
            # read in file and convert to tableau
            data.set(to_tableau(input['file']()))

    # Tableau render function
    @render.data_frame
    def render_tableau():
        if input['file']():
            if solutions(): # if tableau is solved
                return weights_and_harmonies( # display tableau with weights and harmony
                    data(),
                    solutions()[int(input['sol_index']()[-1]) - 1] # solution selected in select_solution
                )
            return tidy_tableaux(data()) # otherwise display without weights and harmony
    
    # Tableau solver
    @reactive.Effect
    @reactive.event(input['solve'])
    def _():
        if input['file']():
            solutions.set(solve_language(data()))
            sol_text.set(create_solution_table(data(), solutions()))
        else:
            ui.modal_show(ui.modal('No tableau found.'))

    # Render solution text
    @render.text
    def solution_text():
        return sol_text()
    
    # Select which solution to show
    @render.ui
    def select_solution():
        if solutions(): # show only if tableau is solved
            return ui.input_selectize(
                'sol_index',
                'Select solution to apply',
                [*map(lambda i: f'Solution {i + 1}', range(len(solutions())))]
            )

app = App(app_ui, server)
