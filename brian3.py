'''
Hopefully closer to the final version (work in progress)

### Yet to be implemented:
- Input UI with HR implemented
- Solving tableau & applying solution

### In the future:
- refine reactive dependency (ss(input['input_urs']()) or data()?)
'''

from common import *


app_ui = ui.page_sidebar(
    ### INPUT PORTION (SIDEBAR) ###
    ui.sidebar(
        ui.panel_title('Shiny HG'),
        ui.markdown('**Build & Edit Tableau**'),
        ui.input_file('file', 'Upload CSV'),
        ui.output_ui('ui_cs'),
        ui.output_ui('ui_urs'),
        ui.output_ui('ui_hr_check'),
        ui.output_ui('ui_srs'),

        open='always',
        width='30%',
    ),

    ### OUTPUT PORTION (MAIN) ###
    ui.output_text('test_output'), # for debugging

    ui.input_action_button('solve', 'Solve', width='150px', class_='btn-primary'),
    ui.output_text('solve_result'),
    ui.output_ui('select_solution'),
    ui.output_data_frame('render_tableau'),
)


def server(input, output, session):
    ### REACTIVE VALUES ###
    

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
    def ui_srs():
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
                    ui.p(id=f'ui_{i_ur}_viols'),
                    ui.p(id=f'ui_{i_ur}_winner')
                )
            )
        return ui.navset_card_underline(*navs)
    
    @reactive.effect
    def _():
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            navs = []
            for i_sr, sr in enumerate(ss(input[f'input_{i_ur}_srs']())):
                nums = []
                for i_c, c in enumerate(ss(input['input_cs']())):
                    uploaded = viols(to_tableau(input['file']()), c, sr) if input['file']() else 0
                    nums.append(
                        ui.input_numeric(
                            f'input_{i_ur}_{i_sr}_viols_{i_c}',
                            f'Enter {c} violation count of {sr}',
                            uploaded,
                            min=0
                        )
                    )
                navs.append(ui.nav_panel(sr, nums))
            render_ui(ui.navset_card_underline(*navs), f'ui_{i_ur}_viols')
    
    @reactive.effect
    def _():
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            uploaded = get_winner(to_tableau(input['file']()), ur) if input['file']() else None
            buttons = ui.input_radio_buttons(
                f'input_{i_ur}_winner',
                f'Select winner of {ur}',
                ss(input[f'input_{i_ur}_srs']()),
                selected=uploaded
            ) if input[f'input_{i_ur}_srs']() else None
            render_ui(buttons, f'ui_{i_ur}_winner')


    ### OUTPUT UI RENDER FNS ###
    # for various tests
    @render.text
    def test_output():
        return
    
    @render.data_frame
    def render_tableau():
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

        return render.DataGrid(tidy_tableaux(tableau), height=None)


app = App(app_ui, server)
