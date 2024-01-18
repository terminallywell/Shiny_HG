'''
Hopefully closer to the final version (work in progress)

Currently implemented:
- constraints, ur, sr, sr violations, sr candidate winner selection
- upload csv to update constraints and ur input
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
    data = reactive.Value(dict())
    winner = reactive.Value(dict())
    

    ### INPUT UI RENDER FNS ###
    @render.ui
    def ui_cs():
        return ui.input_text_area(
            'input_cs',
            'Enter constraints',
            value='c1, c2', # XXX
            placeholder='Enter names of the constraints, separated by commas'
        )

    @render.ui
    def ui_urs():
        return ui.input_text_area(
            'input_urs',
            'Enter URs',
            value='bada, lolo', # XXX
            placeholder='Enter underlying representations (words), separated by commas'
        )
    
    @render.ui
    def ui_srs():
        navs = []
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            navs.append(
                ui.nav_panel(
                    ur,
                    ui.input_text_area(
                        # int index is used in ids instead of literal strings bc ids don't support special characters e.g. periods
                        f'input_{i_ur}_srs',
                        f'Enter SRs of {ur}',
                        placeholder=f'Enter surface representations of {ur} separated by commas'
                    ),
                    ui.p(id=f'ui_{i_ur}_viols'),
                    ui.p(id=f'ui_{i_ur}_winner')
                )
            )
        return ui.navset_card_underline(*navs, footer=ui.output_ui('ui_hr_check'))
    
    @reactive.effect
    def _():
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            navs = []
            for i_sr, sr in enumerate(ss(input[f'input_{i_ur}_srs']())):
                nums = []
                for i_c, c in enumerate(ss(input['input_cs']())):
                    nums.append(
                        ui.input_numeric(
                            f'input_{i_ur}_{i_sr}_viols_{i_c}',
                            f'Enter {c} violation count of {sr}',
                            0,
                            min=0
                        )
                    )
                navs.append(ui.nav_panel(sr, nums))
            render_ui(ui.navset_card_underline(*navs), f'ui_{i_ur}_viols')
    
    @reactive.effect
    def _():
        for i_ur, ur in enumerate(ss(input['input_urs']())):
            buttons = ui.input_radio_buttons(
                f'input_{i_ur}_winner',
                f'Select winner of {ur}',
                ss(input[f'input_{i_ur}_srs']())
            ) if input[f'input_{i_ur}_srs']() else None
            render_ui(buttons, f'ui_{i_ur}_winner')
    
    @render.ui
    def ui_hr_check():
        return ui.tooltip(
            ui.input_switch('input_hr_check', 'Enable hidden representations'),
            '*Explanation about HR*'
        )


    ### INPUT UI UPDATE FNS ###
    @reactive.effect
    def _():
        if input['file']():
            cs = get_constraint_names(to_tableau(input['file']()))
            ui.update_text(
                'input_cs',
                value=', '.join(cs)
            )
    
    @reactive.effect
    def _():
        if input['file']():
            urs = gen_URlist(to_tableau(input['file']()))
            ui.update_text(
                'input_urs',
                value=', '.join(urs)
            )
    
    # and more like this...
    

    ### INPUT PROCESSING FNS ###
    @reactive.effect
    def _():
        data.set(dict())


    ### OUTPUT UI RENDER FNS ###
    # for various tests
    @render.text
    def test_output():
        return str(data())


app = App(app_ui, server)
