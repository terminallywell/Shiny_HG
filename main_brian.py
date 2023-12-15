'''Main application (Brian's version)'''

from common import *


app_ui = ui.page_fluid(
    ui.panel_title("Shiny HG Solver"),

    ui.layout_sidebar(

        ui.panel_sidebar(
            ui.input_file('file', 'Upload tableau'), # upload tableau csv file
            ui.input_action_button('solve', 'Solve', class_="btn-primary"),
            ui.output_text_verbatim('show_solution'), # display solution
        ),

        ui.panel_main(
            ui.output_data_frame('df'), # display tableau
        )
    )
)


def server(input, output, session):
    data = reactive.Value() # tableau data
    sol = reactive.Value() # solution text

    # tableau data and solution text updater
    @reactive.Effect
    def set():
        sol.set('Solutions will be displayed here.') # clear solution text every time file is uploaded
        if input['file'](): # suppress error until file uploaded
            data.set(read_file(input['file']()[0]["datapath"][:-4]))

    # display tableau
    @render.data_frame
    def df():
        if input['file'](): # suppress error until file uploaded
            return tidy_tableaux(data())

    # This is the solving & solution formatting part
    @reactive.Effect
    @reactive.event(input['solve'])
    def solution():
        if input['file'](): # if there is a file
            # solve language
            solutions = solve_language(data())

            # format solutions
            if 'HR' in (columns := data().columns):
                names = columns[4:]
            else:
                names = columns[3:]
            
            sol.set(solutions_pretty(list(names), solutions)) # set solution text

        else: # if no file is uploaded
            ui.modal_show(ui.modal('No file has been uploaded.'))

    # display solution
    @render.text
    def show_solution():
        return sol()


app = App(app_ui, server)
