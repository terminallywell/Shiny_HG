'''Ellie's attempt'''

from common import *


# Create the UI
app_ui = ui.page_fluid(
    ui.navset_tab_card(
        # Create a first tab for simple user uploading
        ui.nav("Upload tableau", 
               ui.layout_sidebar(
                    ui.panel_sidebar(
                        # User upload
                        ui.input_file("file", "Choose file"),

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
                        # Displays for troubleshooting
                        ui.output_text_verbatim("intermediate_constraints"),
                        ui.output_text_verbatim("intermediate_URs"),
                        #ui.output_text_verbatim("intermediate_rep_dict", placeholder="Display dictionary here"),

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
    tableau_data = reactive.Value()
    current_constraints = reactive.Value()
    current_URs = reactive.Value()
    dictionary_of_representations = reactive.Value()

    # If the user has input any URs, create a tab for each
    @render.ui
    def modify_with_input_UR():
        if input['input_URs']():
            navs = []
            UR_list = current_URs()

            for UR in UR_list:
                navs.append(
                    ui.nav(UR,
                        #ui.input_text(f"input_SR_{UR}", f"Enter possible surface representations of {UR} separated by commas"),
                        #ui.input_checkbox("enable_HRs", "Enable HRs"),
                        ui.output_ui("modify_with_input_SR"),
                    )
                )
            return ui.navset_card_tab(*navs)

    # Access and display the current constraints inputted by the user into the top display textbox (updates in real time)
    @reactive.Effect
    def display_current_constraints():
        current_constraints.set(ss(input['input_constraints']()))
    @render.text
    def intermediate_constraints():
        return current_constraints()
    
    # Access and display the current URs inputted by the user into the top display textbox (updates in real time)
    @reactive.Effect
    def display_current_URs():
        current_URs.set(ss(input['input_URs']()))
    @render.text
    def intermediate_URs():
        return current_URs()
    
    '''@reactive.Effect
    def create_dictionary_of_representations():
        representation_dictionary = {}
        current_URs = prepare_reps(input['input_URs']())
        for UR in current_URs:
            current_SRs = f'input_SR_{UR}'
            if input['current_SRs']():
                representation_dictionary[f'{UR}'] = current_SRs
            else:
                representation_dictionary[f'{UR}'] = "placeholder"
        dictionary_of_representations.set(current_URs)
    
    @render.text
    def intermediate_rep_dict():
        if not bool(dictionary_of_representations):
            return dictionary_of_representations
        else:
            return dictionary_of_representations'''
    
    '''@output
    @render.data_frame
    def BYO_user_data_table():
        df = pd.DataFrame()

        # Collect all the user input, if applicable
        constraint_list = prepare_reps(input['input_constraints']())
        UR_list = representation_dict().keys()
        SR_list = representation_dict().values()

        final_UR_column = []
        for UR in UR_list:
            final_UR_column.append(UR)
            corresponding_SRs = representation_dict()[f'{UR}']
            num_gaps_to_insert = len(corresponding_SRs) - 1
            final_UR_column.append(np.repeat("-", num_gaps_to_insert))
        df['UR'] = final_UR_column
        if input['input_SRs']: df['SR'] = SR_list
        #if input['input_HRs'](): df['HR'] = HR_list
        #df['Obs'] = ['-', '-', '1', '-', '-', '-', '1', '-']
        for constraint in constraint_list:
            df[f'{constraint}'] = [1, 1, 0, 0, 1, 0, 1, 0]

        return df'''

app = App(app_ui, server)
