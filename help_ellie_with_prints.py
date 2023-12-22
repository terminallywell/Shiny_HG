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

    # If the user has input any URs, create a tab for each
    @reactive.effect(priority=100)
    @render.ui
    def modify_with_input_UR():
        navs = []
        UR_list = current_URs()
        eprint(f"modify_with_input_UR(): UR_list={UR_list}")
        for UR in UR_list:
            key = f"input_SR_{UR}"
            if key in input_boxes:
                eprint(f"{datetime.datetime.now()}: reused input_text_handle {key}")
                input_text_handle = input_boxes[key]
            else:
                input_text_handle = ui.input_text(key, f"Enter possible SRs of {UR} separated by commas")
                eprint(f"{datetime.datetime.now()}: Created new input_text_handle {key}")
                input_boxes[key] = input_text_handle
            new_nav_element = ui.nav_panel(UR,
                    ui.p(f"The name of this textbox is input_SR_{UR}"),
                    input_text_handle,
                    ui.input_checkbox("enable_HRs", "Enable HRs (currently does nothing)"),
                    #ui.output_ui(f"modify_with_input_SR"),
                )
            navs.append(new_nav_element)
        eprint(f'Tabs being created at {datetime.datetime.now()}')
        return ui.navset_card_tab(*navs)

    # Create way to update tableau and solutions when necessary
    # Create way to update user input value display in real time
    @reactive.effect(priority=100)
    def set():
        solution_text.set("Solutions will be displayed here")
        # Hides error if no file uploaded yet
        if input['file']():
            tableau_data.set(to_tableau(input['file']()))

        current_constraints.set([])
        current_URs.set([])

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
    @reactive.effect(priority=50)
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

    # Access and display the current constraints input by the user into the top display textbox (updates in real time)
    @reactive.effect(priority=50)
    def display_current_constraints():
        current_constraints.set(ss(input['input_constraints']()))
    
    # Access and display the current URs input by the user into the top display textbox (updates in real time) **SHOULD BUT DOESN'T??? WHY
    @reactive.effect(priority=50)
    def display_current_URs():
        current_URs.set(ss(input['input_URs']()))
    
    #@output
    @reactive.effect(priority=-100)
    @render.data_frame
    def BYO_user_data_table():
        eprint('------------------------------------------------')
        eprint(f'Time at loop start is {datetime.datetime.now()}, starting tab generation')
        #reactive.invalidate_later(5)
        df = pd.DataFrame()

        # Collect all the user input, if applicable
        constraint_list = ss(input['input_constraints']())
        underlying_rep_list = ss(input['input_URs']())
        eprint(f'Tabs have been created at {datetime.datetime.now()}')
        eprint(f'URs are {underlying_rep_list}')
        
        surface_rep_list = list()
        for UR in underlying_rep_list:
            eprint(f'UR is "{UR}"   ==input_SR_{UR}==')
            eprint(f"{datetime.datetime.now()}: ", input.__dict__)
            eprint(f"{datetime.datetime.now()}: ", input_boxes)
            eprint(f"{datetime.datetime.now()}: ", input[f'input_SR_{UR}']())
            eprint(f"{datetime.datetime.now()}: ", str(input[f'input_SR_{UR}']()))
            if f'input_SR_{UR}' in input:
                items = ss(input[f'input_SR_{UR}']())
            else:
                items = [ '!']
            if len(items) == 0:
                items = [ '?' ]
            eprint(f"items is {items}")
            surface_rep_list.extend(items)
            eprint(f'SRs are {surface_rep_list}')

        # Initialize an empty UR column to be edited based on presence of SRs
        final_UR_column = []
        for UR in underlying_rep_list:
            # Append the current UR to the list
            final_UR_column.append(UR)
            eprint(f'final_UR_column is currently {final_UR_column}')
            # Only worry about adding gaps if there are SRs inserted for this particular UR
            if f'input_SR_{UR}' in input:
                if input[f'input_SR_{UR}']():
                    num_corresponding_SRs = len(ss(input[f'input_SR_{UR}']()))
                    eprint(f'number of SRs is {num_corresponding_SRs}')
                    if num_corresponding_SRs > 1:
                        final_UR_column.extend(np.repeat("-", num_corresponding_SRs - 1))
                        eprint(f'final_UR_column is now {final_UR_column}')

        # Only show UR column if there is user input to prevent random floating box
        if input['input_URs']():
            df['UR'] = final_UR_column
            df['SR'] = surface_rep_list
            df['Obs'] = np.repeat("-", len(final_UR_column))

        # Add each constraint as a column with the constraint name as the header and placeholder values for now
        for constraint in constraint_list:
            df[f'{constraint}'] = np.repeat("-", len(final_UR_column))

        eprint(f'Table being generated at {datetime.datetime.now()}')
        return df

app = App(app_ui, server)
