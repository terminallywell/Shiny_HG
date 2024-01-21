'''
Hopefully closer to the final version (work in progress)

### Yet to be implemented:
- Solving tableau & applying solution
    - Error handling (incomplete tableau)

### Bugs:
1. no radio button selected by default if file uploaded but new ur/sr added
1. Uploading tableau sorts entries alphabetically (intentional?)
1. "UnboundLocalError: cannot access local variable 'winner_id' where it is not associated with a value"
   in add_tableau when solving language
   Last 2 bugs likely have something to do with `np.unique()` used in `gen_SR()` etc. sorting items

### In the future:
- Refine reactive dependency (ss(input['input_urs']()) or data()?)
- Manicules instead of Obs column
- Credits
- Themes & dark mode/light mode
- Hide empty navsets and radio buttons
- Click row to set as winner

### Technical limitations:
- Editing a text input resets all other inputs below (due to the way `render_ui()` is implemented)
- Extremely laggy especially with HRs
    - Try modules?
'''

from common import *


app_ui = ui.page_sidebar(
    ### INPUT PORTION (SIDEBAR) ###
    ui.sidebar(
        ui.markdown('**Build & Edit Tableau**'),
        ui.input_file('file', 'Upload existing tableau (CSV)'),
        ui.hr(),
        ui.output_ui('ui_cs'),
        ui.output_ui('ui_urs'),
        ui.output_ui('ui_hr_check'),
        ui.output_ui('ui_navset_layer1'),
        ui.download_button('save', 'Save tableau as CSV (Not working yet)'),

        open='always',
        width='30%',
    ),

    ### OUTPUT PORTION (MAIN) ###
    ui.output_text('test_output'), # for debugging

    ui.input_action_button('solve', 'Solve', width='150px', class_='btn-primary'),
    ui.output_text('solve_result'),
    ui.output_ui('select_solution'),
    ui.output_data_frame('render_tableau'),
    
    shinyswatch.theme.journal(),

    title='Shiny HG',
)


def server(input, output, session):
    ### REACTIVE VALUES ###
    solutions = reactive.Value()

    ### INPUT UI RENDER FNS ###
    @render.ui
    def ui_cs():
        uploaded = ', '.join(get_constraint_names(to_tableau(input['file']()))) if input['file']() else ''
        return ui.input_text_area(
            'input_cs',
            'Enter constraints',
            value=uploaded,
            placeholder='Enter names of the constraints, separated by commas'
        )

    @render.ui
    def ui_urs():
        uploaded = ', '.join(gen_URlist(to_tableau(input['file']()))) if input['file']() else ''
        return ui.input_text_area(
            'input_urs',
            'Enter URs',
            value=uploaded,
            placeholder='Enter underlying representations (words), separated by commas'
        )
    
    @render.ui
    def ui_hr_check():
        return ui.tooltip(
            ui.input_switch('input_hr_check', 'Enable hidden representations'),
            '*Explanation about HR*',
        )

    @reactive.effect
    def update_hr_check():
        if input['file']():
            ui.update_switch('input_hr_check', value='HR' in to_tableau(input['file']()).columns)
    
    @render.ui
    def ui_navset_layer1():
        '''1st navset layer, where SRs of each UR are entered and winners selected.'''
        navs = []
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            uploaded = ', '.join(gen_SR(to_tableau(input['file']()), ur)) if input['file']() else ''
            navs.append(
                ui.nav_panel(
                    ur,
                    ui.input_text_area(
                        # int index is used in ids instead of literal strings bc ids don't support special characters e.g. periods
                        f'input_{i_ur}_srs',
                        f'Enter SRs of {ur}',
                        value=uploaded,
                        placeholder=f'Enter surface representations (candidates) of {ur}, separated by commas'
                    ),
                    ui.output_ui(f'ui_{i_ur}_navset_layer2'),
                    ui.output_ui(f'ui_{i_ur}_winner')
                )
            )
        return ui.navset_card_tab(*navs)
    
    @reactive.effect
    def ui_navset_layer2():
        '''2nd navset layer, where violation counts (if no HR) or HRs (if HR) of each SR are entered.'''
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            navs = []
            for i_sr, sr in enumerate(ss(input[f'input_{i_ur}_srs']())):

                ## HR ENABLED ##
                if input['input_hr_check'](): # fill navset with HR inputs
                    uploaded = ''
                    if input['file']() and 'HR' in to_tableau(input['file']()).columns:
                        uploaded = ', '.join(get_HRs(to_tableau(input['file']()), ur, sr))
                    
                    uis = [
                        ui.input_text_area(
                            f'input_{i_ur}_{i_sr}_hrs',
                            f'Enter HRs of {sr}',
                            value=uploaded,
                            placeholder=f'Enter hidden representations of {sr}, separated by commas'
                        ),
                        ui.output_ui(f'ui_{i_ur}_{i_sr}_navset_layer3')
                    ]

                ## HR DISABLED ##
                else: # fill navset with SR violation inputs
                    uis = []
                    for i_c, c in enumerate(ss(input['input_cs']())):
                        uploaded = get_viols(to_tableau(input['file']()), c, ur, sr) if input['file']() else 0
                        uis.append(
                            ui.input_numeric(
                                f'input_{i_ur}_{i_sr}_viols_{i_c}',
                                ui.markdown(f'Enter **{c}** violation count'),
                                uploaded,
                                min=0
                            )
                        )

                navs.append(ui.nav_panel(sr, uis))
            render_ui(ui.navset_card_tab(*navs), f'ui_{i_ur}_navset_layer2')

    @reactive.effect
    def ui_navset_layer3():
        '''3rd navset layer, where violation counts of each HR are entered (only shows when HR enabled).'''
        if input['input_hr_check'](): # this line is only here for reactive purposes
            for i_ur, ur in enumerate(ss(input['input_urs']())):
                for i_sr, sr in enumerate(ss(input[f'input_{i_ur}_srs']())):
                    navs = []
                    for i_hr, hr in enumerate(ss(input[f'input_{i_ur}_{i_sr}_hrs']())):
                        uis = []
                        for i_c, c in enumerate(ss(input['input_cs']())):
                            uploaded = get_viols(to_tableau(input['file']()), c, ur, sr, hr) if input['file']() else 0
                            uis.append(
                                ui.input_numeric(
                                    f'input_{i_ur}_{i_sr}_{i_hr}_viols_{i_c}',
                                    ui.markdown(f'Enter **{c}** violation count'),
                                    uploaded,
                                    min=0
                                )
                            )
                        navs.append(ui.nav_panel(hr, uis))
                    render_ui(ui.navset_card_tab(*navs), f'ui_{i_ur}_{i_sr}_navset_layer3')
    
    @reactive.effect
    def ui_winner():
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            uploaded = get_winner(to_tableau(input['file']()), ur) if input['file']() else None # BUG 1
            buttons = ui.input_radio_buttons(
                f'input_{i_ur}_winner',
                f'Select winner of {ur}',
                ss(input[f'input_{i_ur}_srs']()),
                selected=uploaded
            ) if input[f'input_{i_ur}_srs']() else None
            render_ui(buttons, f'ui_{i_ur}_winner')
    

    ### INPUT PROCESSING FNS ###
    @reactive.calc
    def build_tableau():
        '''Builds tableau `DataFrame` from inputs.'''
        urs = []
        srs = []
        obs = []
        hrs = []
        cs = {}

        for i_ur, ur in enumerate(ss(input['input_urs']())):
            for i_sr, sr in enumerate(ss(input[f'input_{i_ur}_srs']())):
                if input['input_hr_check'](): # if HR enabled
                    obs_added = False
                    for i_hr, hr in enumerate(ss(input[f'input_{i_ur}_{i_sr}_hrs']())):
                        urs.append(ur) # fill UR column
                        srs.append(sr) # fill SR column
                        if sr == input[f'input_{i_ur}_winner']() and not obs_added:
                            obs.append(1) # fill Obs column
                            obs_added = True # only add one Obs marker for each winner
                        else:
                            obs.append(nan)
                        hrs.append(hr)
                        for i_c, c in enumerate(ss(input['input_cs']())):
                            cs.setdefault(c, []).append(input[f'input_{i_ur}_{i_sr}_{i_hr}_viols_{i_c}']()) # fill C columns
                else:
                    urs.append(ur)
                    srs.append(sr)
                    obs.append(1 if sr == input[f'input_{i_ur}_winner']() else nan)
                    for i_c, c in enumerate(ss(input['input_cs']())):
                        cs.setdefault(c, []).append(input[f'input_{i_ur}_{i_sr}_viols_{i_c}']())
        
        tableau = pd.DataFrame()
        tableau['UR'] = urs
        tableau['SR'] = srs
        tableau['Obs'] = obs
        if input['input_hr_check']():
            tableau['HR'] = hrs
        for c in cs:
            tableau[c] = cs[c]

        return tableau

    @reactive.effect
    @reactive.event(input['solve'])
    def solver():
        solutions.set(solve_language(build_tableau()))
    

    ### OUTPUT UI RENDER FNS ###
    # For debugging purposes
    @render.text
    def test_output():
        return f'{build_tableau().__repr__()}'
        # return req(input['render_tableau_selected_rows']())
    
    
    @output
    @render.data_frame()
    def render_tableau():
        '''Renders tableau, with solution applied if available.'''
        return render.DataGrid(tidy_tableaux(build_tableau()), row_selection_mode='none', height=None)


app = App(app_ui, server)
