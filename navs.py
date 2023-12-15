'Dynamic UI demo'

from common import *


app_ui = ui.page_fluid(
    ui.input_text_area('input_urs', 'Enter URs', 'this, is, sample, text'),
    ui.output_ui('ur_modify')
)


def server(input, output, session):
    
    @render.ui
    def ur_modify():
        navs = []

        urs = ss(input['input_urs']())

        for ur in urs:
            navs.append(
                ui.nav(
                    ur,
                    f'Here you will edit SRs for "{ur}"'
                )
            )

        return ui.navset_card_tab(*navs)


app = App(app_ui, server)
