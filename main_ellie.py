'''Ellie's attempt'''

from common import *

input_boxes = {}


# Create the UI
app_ui = ui.page_fluid(
    ui.navset_card_tab(
        # Create a first tab for simple user uploading
        ui.nav_panel("Upload tableau", 
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

                        # Create tab sections for adding constraint violations for each SR input
                        ui.p("Note constraint violations for your SRs"),
                        ui.output_ui("input_violations"),

                        # Initiate Solve
                        ui.input_action_button("BYO_solve", "Solve!", class_="btn-primary"),

                        # Display solution when solved
                        ui.output_text_verbatim("BYO_solutions_output"),
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
    @reactive.effect()
    def set():
        solution_text.set("Solutions will be displayed here")
        # Hides error if no file uploaded yet
        if input['file']():
            tableau_data.set(to_tableau(input['file']()))

        current_constraints.set([])
        current_URs.set([])
        BYO_solution_text.set("Solutions will be displayed here")

    # Generate a tidy tableau of user data whenever a new file is uploaded
    @reactive.calc
    def gen_user_data_table():
        if input['file']():
            return tidy_tableaux(to_tableau(input['file']()))
    
    # Render the new tidy tableau
    @render.table()
    def user_data_table():
        return gen_user_data_table()

    # Generate the solution set whenever a new file is uploaded
    @reactive.calc
    def gen_solution_set():
        return create_solution_table(
            to_tableau(input['file']()),
            solve_language(to_tableau(input['file']()))
        )
    
    # When the user tries to solve, if there is a file, generate the solution(s)
    @reactive.effect()
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
    BYO_solution_text = reactive.Value()

    # Access and display the current constraints input by the user into the top display textbox (updates in real time)
    @reactive.effect()
    def display_current_constraints():
        current_constraints.set(ss(input['input_constraints']()))
    
    # Access and display the current URs input by the user into the top display textbox (updates in real time) **SHOULD BUT DOESN'T??? WHY
    @reactive.effect()
    def display_current_URs():
        current_URs.set(ss(input['input_URs']()))
    
    # Show the new solution(s)
    @render.text
    def BYO_solutions_output():
        return BYO_solution_text()

    # If the user has input any URs, create a tab for each
    @reactive.effect()
    @render.ui
    def modify_with_input_UR():
        navs = []
        UR_list = current_URs()
        for UR in UR_list:
            navs.append(
                ui.nav_panel(UR,
                    ui.input_text(f'input_SR_{UR}', f"Enter possible SRs of {UR} separated by commas"),
                    ui.input_text(f'select_winner_{UR}', f"Enter the ONE winner candidate for {UR}"),
                    ####THESE LINES BREAK THE WHOLE CODE ENABLE AT YOUR OWN RISK
                    #ui.input_checkbox("enable_HRs", "Enable HRs (currently does nothing)"),
                    #ui.output_ui(f"modify_with_input_SR"),
                )
            )
        return ui.navset_card_tab(*navs)
    
    # If the user has input any constraints, create a tab for each
    @reactive.effect()
    @render.ui
    def input_violations():
        viol_navs = []
        constraint_list = current_constraints()
        for constraint in constraint_list:
            viol_navs.append(
                ui.nav_panel(constraint,
                    ui.input_text(f'input_viol_{constraint}', f"Enter each SR that violates {constraint} separated by commas"),
                )
            )
        return ui.navset_card_tab(*viol_navs)
    
    
    # Dynamically update the table when the user adds input
    @reactive.effect()
    @render.data_frame
    def BYO_user_data_table():
        df = pd.DataFrame()

        # Collect the user constraints
        constraint_list = ss(input['input_constraints']())

        # Collect the user URs
        underlying_rep_list = ss(input['input_URs']())

        # Collect the user SRs
        surface_rep_list = list()
        for UR in underlying_rep_list:
            if f'input_SR_{UR}' in input:
                items = ss(input[f'input_SR_{UR}']())
            else:
                items = ['-']
            if len(items) == 0:
                items = [ '-' ]
            surface_rep_list.extend(items)        

        # Initialize an empty UR column to be edited based on presence of SRs
        final_UR_column = []
        for UR in underlying_rep_list:
            # Append the current UR to the list
            final_UR_column.append(UR)
            # Only worry about adding gaps if there are SRs inserted for this particular UR
            if f'input_SR_{UR}' in input:
                if input[f'input_SR_{UR}']():
                    num_corresponding_SRs = len(ss(input[f'input_SR_{UR}']()))
                    if num_corresponding_SRs > 1:
                        final_UR_column.extend(np.repeat("-", num_corresponding_SRs - 1))
        
        # Initialize an empty OBS column to be edited based on the chosen winner candidates
        obs_column = np.repeat("0", len(final_UR_column))
        # Get the user-specified winners
        winner_list = []
        for UR in underlying_rep_list:
            if input[f'select_winner_{UR}']():
                winner_list.append(input[f'select_winner_{UR}']())
        # If the current winner matches anything in the surface representation list, replace that index in the obs list with 1
        for winner_cand in winner_list:
            if winner_cand in surface_rep_list:
                obs_column[surface_rep_list.index(winner_cand)] = 1

        # Only show columns if there is user input to prevent random floating box
        if input['input_URs']():
            df['UR'] = final_UR_column
            df['SR'] = surface_rep_list           
            df['Obs'] = obs_column
        
        # Collect the user violation vectors into a dictionary with the format {constraint: list of violators}
        constraint_viol_dict = dict()
        for constraint in constraint_list:
            if f'input_viol_{constraint}' in input:
                constraint_viol_dict[f'{constraint}'] = ss(input[f'input_viol_{constraint}']())
            else:
                constraint_viol_dict[f'{constraint}'] = "-"

        # Add each constraint as a column with the constraint name as the header and placeholder values for now
        for constraint in constraint_list:
            temp_column = np.repeat("-", len(final_UR_column))
            viol_list = constraint_viol_dict[f'{constraint}']

            for violator in viol_list:
                if violator in surface_rep_list:
                    temp_column[surface_rep_list.index(violator)] = 1

            df[f'{constraint}'] = temp_column
        
        # Generate the solution set whenever a change is made
        @reactive.calc
        def BYO_gen_solution_set():
            eprint("In BYO_gen_sol_set function")
            eprint(f'solution table is {create_solution_table}')
            return create_solution_table(
                df,
                solve_language(df)
            )
        
        # Initiate solve
        @reactive.effect()
        @reactive.event(input['BYO_solve'])
        def solve_user_input():
            eprint("----------------------------")
            eprint(f'trying to solve')
            eprint(f'BYO_gen_solution_set_is {BYO_gen_solution_set}')
            BYO_solution_text.set(BYO_gen_solution_set())

        return df

app = App(app_ui, server)
