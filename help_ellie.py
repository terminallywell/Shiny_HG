'''Ellie's attempt'''

from common import *


# Create the UI
app_ui = ui.page_fluid(
    ui.navset_card_tab(
        # Create a first tab for simple user uploading
        ui.nav("Upload tableau", 
               ui.layout_sidebar(
                    ui.panel_sidebar(
                        # User upload
                        ui.input_file("file", "Choose file", button_label='Browse...', placeholder='No file selected'),

                        # Initiate Solve
                        ui.input_action_button("solve", "Solve!", class_="btn-primary"),

                        # Display solution when solved
                        ui.output_text_verbatim("solutions_output"),
                    ),
                    ui.panel_main(
                        # Display tableau uploaded by user
                        ui.output_table("user_data_table"),
                    ),
            ),
        ),
        # Create a second tab for interactivity
        ui.nav("Build your own tableau", 
            ui.layout_sidebar(
                    ui.panel_sidebar(
                        # User upload
                        ui.input_text("input_constraints", "Enter a list of constraints separated by commas"),
                        ui.input_text("input_URs", "Enter a list of URs separated by commas"),

                        # Create tab sections for adding SR inputs for each UR input
                        ui.p("Add surface representations for your URs"),
                        ui.output_ui("modify_with_input_UR"),

                        # Create sections for adding HR inputs for each UR input, if applicable
                        #ui.p("Add hidden representations for your SRs"),
                        #ui.output_ui("modify_with_input_SR"),
                    ),
                    ui.panel_main(
                        # Display tableau uploaded by user
                        ui.output_data_frame("BYO_user_data_table"),
                    ),
            ),
        ),
    )
)

def server(input, output, session):
    #############################################################
    ###########This section is for the user upload tab###########
    #############################################################

    # Initialize values for the user tableau and the solution set
    tableau_data = reactive.Value()
    solution_text = reactive.Value()

    # Create way to update tableau and solutions when necessary
    # Create way to update user input value display in real time
    @reactive.Effect
    def set():
        solution_text.set("Solutions will be displayed here")
        # Hides error if no file uploaded yet
        if input['file']():
            tableau_data.set(to_tableau(input['file']()))

        current_constraints.set("Display current constraints here")
        current_URs.set("Display current URs here")
        dictionary_of_representations.set("Display dictionary here")

    # Generate a tidy tableau of user data whenever a new file is uploaded
    @reactive.Calc
    def gen_user_data_table():
        if input['file']():
            return tidy_tableaux(to_tableau(input['file']()))
    
    # Render the new tidy tableau
    @render.table()
    def user_data_table():
        return gen_user_data_table()

    # Generate the solution set whenever a new file is uploaded
    @reactive.Calc
    def gen_solution_set():
        return create_solution_table(
            to_tableau(input['file']()),
            solve_language(to_tableau(input['file']()))
        )
    
    # When the user tries to solve, if there is a file, generate the solution(s)
    @reactive.Effect
    @reactive.event(input['solve'])
    def solutions_text():
        if input['file']():
            solution_text.set(gen_solution_set())
    #Otherwise, give prompt to upload
        else:
            ui.modal_show(ui.modal("Please upload a file"))

    # Show the new solution(s)
    @render.text
    def solutions_output():
        return solution_text()
    
    #############################################################
    ###########This section is for the BYO tableau tab###########
    #############################################################
    # Initialize reactive values to get current user inputs
    current_constraints = reactive.Value()
    current_URs = reactive.Value()
    dictionary_of_representations = reactive.Value()

    # If the user has input any URs, create a tab for each
    #@reactive.Effect
    @render.ui
    def modify_with_input_UR():
        navs = []
        UR_list = current_URs()

        for UR in UR_list:
            navs.append(
                ui.nav(UR,
                    ui.input_text(f"input_SR_{UR}", f"Enter possible SRs of {UR} separated by commas"),
                    ui.input_checkbox("enable_HRs", "Enable HRs (currently does nothing)"),
                    ui.output_ui(f"modify_with_input_SR"),
                )
            )
        return ui.navset_card_tab(*navs)

    # Access and display the current constraints input by the user into the top display textbox (updates in real time)
    @reactive.Effect
    def display_current_constraints():
        current_constraints.set(ss(input['input_constraints']()))
    
    # Access and display the current URs input by the user into the top display textbox (updates in real time) **SHOULD BUT DOESN'T??? WHY
    @reactive.Effect
    def display_current_URs():
        current_URs.set(ss(input['input_URs']()))
    
    @output
    @render.data_frame
    def BYO_user_data_table():
        df = pd.DataFrame()

        # Collect all the user input, if applicable
        constraint_list = ss(input['input_constraints']())
        underlying_rep_list = ss(input['input_URs']())

        '''if input['input_SRs']: df['SR'] = SR_list
        #if input['input_HRs'](): df['HR'] = HR_list
        #df['Obs'] = ['-', '-', '1', '-', '-', '-', '1', '-']'''
        
        # Initialize an empty UR column to be edited based on presence of SRs
        final_UR_column = []
        #final_SR_column = []
        for UR in underlying_rep_list:
            final_UR_column.append(UR)
            #corresponding_SRs = ss(input[f'input_SR_{UR}']())
            #if len(corresponding_SRs) >= 1:
                #num_gaps_to_insert = len(corresponding_SRs) - 1
                #final_UR_column.append(np.repeat("-", num_gaps_to_insert))
            #final_SR_column.append(corresponding_SRs)

        # Only show UR column if there is user input to prevent random floating box
        if input['input_URs']():
            df['UR'] = final_UR_column
        #df['SR'] = final_SR_column

        # Add each constraint as a column with the constraint name as the header and placeholder values for now
        for constraint in constraint_list:
            df[f'{constraint}'] = np.repeat("-", len(final_UR_column))

        return df

app = App(app_ui, server)
