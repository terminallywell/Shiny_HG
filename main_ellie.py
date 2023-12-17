'''Main application (Ellie's version)'''

from common import *


app_ui = ui.page_sidebar(
    ui.sidebar(
        # User upload
        ui.input_file("file", "Choose file"),

        # Initiate Solve
        ui.input_action_button("solve", "Solve!", class_="btn-primary"),

        # Display solution when solved
        ui.output_text_verbatim("solutions_output"),

        width=400
    ),

    ui.card(
        # Display tableau uploaded by user
        ui.output_table("user_data_table"),
    )
)


def server(input, output, session):
    # Initialize values for the user tableau and the solution set
    tableau_data = reactive.Value()
    solution_text = reactive.Value()

    # Create way to update tableau and solutions when necessary
    @reactive.Effect
    def set():
        solution_text.set("Solutions will be displayed here")
        if input['file']():
            tableau_data.set(read_file(str(input['file']()[0]["datapath"])[:-4]))

    # Create a tidy tableau of user data whenever a new file is uploaded
    @reactive.Calc
    def gen_user_data_table():
        if input['file']():
            return tidy_tableaux(read_file(str(input['file']()[0]["datapath"])[:-4]))
    # Render the new tidy tableau
    @render.table()
    def user_data_table():
        return gen_user_data_table()
    

    # Generate the solution set whenever a new file is uploaded
    @reactive.Calc
    def gen_solution_set():
        if input['file']():
            return create_solution_table(read_file(str(input['file']()[0]["datapath"][:-4])), solve_language(read_file(str(input['file']()[0]["datapath"][:-4]))))
    
    # When the user tries to solve, if there is a file, render the corresponding
    @reactive.Effect
    @reactive.event(input['solve'])
    def solutions_text():
        if input['file']():
            solution_text.set(gen_solution_set())
    #Otherwise, give prompt to upload
        else:
            ui.modal_show(ui.modal("Please upload a file"))

    # Show the new solutions
    @render.text
    def solutions_output():
        return solution_text()


app = App(app_ui, server)
