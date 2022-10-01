# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

from dash import Dash, html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import json


theme = dbc.themes.BOOTSTRAP
app = Dash(
    __name__,
    external_stylesheets=[theme]
)
server = app.server

"""
Load data.
"""
db_name = "demo.csv"
df = pd.read_csv(db_name, sep=";")
# creates an auxiliar column to get original index when filtering
df["original_idx"] = range(len(df))
if "label" not in df.columns.to_list():
    # initialize column "label" with value "no_label"
    df["label"] = "no_label"
print(df)

"""
Dropdown menu to choose specific labels to be shown in the visualization.
"""
sorted_unique_labels = sorted(df.label.unique())
label_filter = html.Div(children=[
    dbc.Label("Filtrar por rótulo"),
    dcc.Dropdown(
        id="label-filter-dropdown",
        options=[{"label": l, "value": l} for l in sorted_unique_labels],
        multi=True,
        value="",
        placeholder="Escolha um rótulo"
    )
])

"""
Input field to filter documents containing the keywords entered.
"""
keyword_filter = html.Div(children=[
    dbc.Label("Filtrar por palavra chave"),
    dbc.InputGroup(children=[
        dbc.Input(
            id="keyword-filter-input",
            type="text",
            placeholder="Digite uma palavra chave"
        ),
        dbc.Button("Adicionar palavra", id="keyword-button")
    ])
])

"""
Accordion showing the selected labels and keywords.
"""
filter_list = html.Div(children=[
    dbc.Accordion(children=[
        dbc.AccordionItem(children=[
            dbc.Checklist(
                inline=True,
                id="keywords-checklist"
            )
        ], title="Palavras chave escolhidas")
    ], start_collapsed=False)
])

"""
Document detail modal.
"""
detail_modal = dbc.Modal(children=[
    dbc.ModalHeader(dbc.ModalTitle("Detalhes do documento")),
    dbc.ModalBody(id="detail-modal-body"),
    dbc.ModalFooter(children=[
        dbc.Button(children="Fechar",
                   id="detail-modal-close")
    ])
], id="detail-modal", is_open=False, size="lg")

"""
Draw projection.
"""
def draw_figure(df, labels=[], keywords=[]):
    # filter by selected labels
    if labels:
        df = df.loc[df.label.isin(labels)]

    # filter by selected keywords
    if keywords:
        for kw in keywords:
            df = df.loc[df.text.str.contains(kw)]

    # draw filtered df
    if labels:
        fig = px.scatter(df, x="x", y="y", color="label", hover_data=["text", "original_idx"])
    else:
        fig = px.scatter(df, x="x", y="y", hover_data=["text", "original_idx"])
    fig.update_traces(marker={
        "line": {
            "width": 1,
            "color": "black"
        }
    })

    return fig

"""
Input field to insert new labels.
"""
create_user_label = html.Div(children=[
    #dbc.Label("Nome do novo rótulo"),
    dbc.InputGroup(children=[
        dbc.Input(
            id="new-label-input",
            type="text",
            placeholder="Novo rótulo"
        ),
        dbc.Button("Adicionar rótulo", id="new-label-button")
    ])
])

"""
Layout definition.
"""
app.layout = dbc.Container(children=[
    dbc.Row(children=[
        dbc.Col(children=[
            html.H1(children="Rotulação de documentos")
        ], md=10),
        dbc.Col(children=[
            html.Div(children=[
                dbc.Button("Finalizar", id="end-labeling-button")
            ], className="d-md-flex justify-content-md-end")
        ]),
        dbc.Alert(id="end-labeling-response", is_open=False, dismissable=True)
    ]),
    html.Hr(),
    dbc.Accordion(children=[
        dbc.AccordionItem(children=[
            dbc.Row(children=[
                dbc.Col(children=[
                    label_filter
                ], md=12)
            ]),
            dbc.Row(children=[
                keyword_filter,
            ]),
            dbc.Row(children=[
                dbc.Col(children=[
                    filter_list
                ], md=12)
            ])
        ], title="Filtros")
    ], start_collapsed=True),
    dbc.Accordion(children=[
        dbc.AccordionItem(children=[
            dbc.Row(children=[
                create_user_label
            ])
        ], title="Inserir rótulos")
    ], start_collapsed=True),
    dbc.Row(children=[
        html.H3("Rotulando '" + db_name + "'"),
        dbc.InputGroup(children=[
            dbc.Col(children=[
                dcc.Dropdown(
                    id="selected-label-dropdown",
                    placeholder="Marque os pontos e selecione o rótulo aqui"
                )
            ], md=11),
            dbc.Col(children=[
                dbc.Button("Rotular", id="set-label-button")
            ], md=1),
        ]),
        dbc.Alert(id="labeling-response", is_open=False, dismissable=True,
                  duration=5000),
        html.Div(children=[
            dcc.Graph(id="projection-graph")
        ])
    ]),
    detail_modal,
    dcc.Store(id="keywords"),
    dcc.Store(id="labels"),
    dcc.Store(id="update-drawing")
])

"""
Callbacks
"""
@app.callback(
    Output("projection-graph", "figure"),
    Input("label-filter-dropdown", "value"),
    Input("keywords", "data"),
    Input("labels", "data"),
    Input("update-drawing", "data"))
def update_figure(selected_labels, keywords, labels, update_drawing):
    """
    Draw figure when labels (Dropdown) or keywords (Store) change.
    """
    print("selected labels", selected_labels)
    if selected_labels:
        return draw_figure(df, labels=selected_labels, keywords=keywords)
    else:
        return draw_figure(df, labels=labels, keywords=keywords)

@app.callback(
    Output("keywords", "data"),
    Output("keyword-filter-input", "value"),
    Input("keyword-button", "n_clicks"),
    Input("keyword-filter-input", "n_submit"),
    Input("keywords", "data"),
    Input("keywords-checklist", "value"),
    State("keyword-filter-input", "value"))
def update_keywords(n_clicks, n_submit, keywords, kw_checklist, new_kw):
    """
    Update keywords on button click, enter key press or checklist changes.
    """
    # https://dash.plotly.com/advanced-callbacks
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(trigger_id)

    if keywords is None:
        keywords = []
    elif trigger_id in ("keyword-filter-input", "keyword-button"):
        if new_kw and (new_kw not in keywords):
            keywords.append(new_kw)
    elif trigger_id == "keywords-checklist":
        keywords = kw_checklist
    print("selected keywords", keywords)
    return [keywords, ""]

@app.callback(
    Output("keywords-checklist", "options"),
    Output("keywords-checklist", "value"),
    Input("keywords", "data"))
def update_kw_list(keywords):
    """
    Update keywords in checkbox when keywords (Store) changes.
    """
    return [[{"label": '"'+kw+'"', "value": kw} for kw in keywords],
            [kw for kw in keywords]]

@app.callback(
    Output("detail-modal", "is_open"),
    Output("detail-modal-body", "children"),
    Input("projection-graph", "clickData"),
    Input("detail-modal-close", "n_clicks"),
    State("detail-modal", "is_open"),
)
def toggle_modal(clickData, close_btn, is_open):
    """
    Toogle document detail modal.
    """
    if clickData or close_btn:
        return [not is_open, clickData["points"][0]["customdata"][0]]
    return [is_open, clickData["points"][0]["customdata"][0]]

@app.callback(
    Output("label-filter-dropdown", "options"),
    Input("labels", "data")
)
def update_label_dropdown(labels):
    """
    Update label Dropdown menu on labels (Store) changes.
    """
    return [{"label": l, "value": l} for l in labels]

@app.callback(
    Output("labels", "data"),
    Output("new-label-input", "value"),
    Input("labels", "data"),
    Input("new-label-button", "n_clicks"),
    Input("new-label-input", "n_submit"),
    State("new-label-input", "value"))
def create_label(labels, n_clicks, n_submit, new_label):
    """
    Create a new label using input.
    """
    # https://dash.plotly.com/advanced-callbacks
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    print(trigger_id)

    if labels is None:
        labels = sorted_unique_labels
    elif trigger_id in ("new-label-input", "new-label-button"):
        if new_label and (new_label not in labels):
            labels.append(new_label)
    print("all labels", labels)
    return [labels, ""]

@app.callback(
    Output("selected-label-dropdown", "options"),
    Input("labels", "data"))
def update_selection_labels(labels):
    """
    Update select label dropdown when labels (Store) change.
    """
    return [{"label": l, "value": l} for l in labels]

@app.callback(
    Output("labeling-response", "children"),
    Output("labeling-response", "is_open"),
    Output("selected-label-dropdown", "value"),
    Output("update-drawing", "data"),
    Input("set-label-button", "n_clicks"),
    State("selected-label-dropdown", "value"),
    State("projection-graph", "selectedData"))
def set_label(n_clicks, label, selectedData):
    """
    Set label for selected points.
    """
    if label:
        print("selectedData:", selectedData)
        selected = [selectedData["points"][i]["customdata"][1] for i in
                    range(len(selectedData["points"]))]
        print("selected:", selected)
        df.loc[selected, "label"] = label
        return ['%d textos rotulados como "%s"' % (len(selected), label), True, "",
                "update"]

@app.callback(
    Output("end-labeling-response", "children"),
    Output("end-labeling-response", "is_open"),
    Input("end-labeling-button", "n_clicks"))
def end_labeling(n_clicks):
    """
    Saves current labeling to file.
    """
    if n_clicks:
        from datetime import datetime as dt
        out_file = db_name[:-4] + "-output-" + dt.now().strftime("%Y%m%d_%H%M%S") + ".csv"
        # drops "original_idx" auxiliar column before saving
        df.drop(["original_idx"], axis=1).to_csv(out_file, sep=";", index=False)
        return ['Rotulação salva no arquivo "' + out_file + '"', True]
    else:
        return ["", False]

if __name__ == "__main__":
    app.run_server(debug=True)
