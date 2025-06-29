import dash
from dash import html, dcc, Input, Output, callback, Dash, State
import plotly.express as px
import pandas as pd
from pathlib import Path
import pycountry
import json
from urllib.request import urlopen
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from math import ceil, isnan


# COLORS 
TEXT_COLOR = "#ffffff"  # white text
BACKGROUND_COLOR = "#171a27"  # dark gray background
BASE_COLOR = "#1f212f"  # slightly lighter gray for the main background
DROPDOWN_BG_COLOR = "#242632"  # dropdown background color
DROPDOWN_HOVER_COLOR = "#31333f"  # dropdown hover color

# STYLE
### ------ Explorative Charts
EXPLORATIVE_HEIGHT = "53vh"
EXPLORATIVE_TITLE_SIZE = 14
EXPLORATIVE_TICK_SIZE = 10
EXPLORATIVE_AXIS_LABEL_SIZE = 11
EXPLORATIVE_LEGEND_FONT_SIZE = 11
EXPLORATIVE_LEGEND_TITLE_SIZE = 12
EXPLORATIVE_OPTIONS_SIZE = "14px"
EXPLORATIVE_HOVER_SIZE = 14
CHOROPLETH_TITLE_SIZE = 20


def name_to_iso3(name):
    if name == "UK":
        name = "United Kingdom"
    try:
        return pycountry.countries.lookup(name).alpha_3
    except LookupError:
        return None
    
def get_choropleth_map():
    url_map = 'https://raw.githubusercontent.com/johan/world.geo.json/master/countries.geo.json'

    with urlopen(url_map) as response:
        geo_data = json.load(response)

    df_grouped = df.groupby("iso_code")["AI Adoption Rate (%)"].mean().reset_index()

    # show country names in the tooltip instead of ISO codes
    iso_to_country = df[['iso_code', 'Country']].drop_duplicates().set_index('iso_code')['Country'].to_dict()
    df_grouped['Country'] = df_grouped['iso_code'].map(iso_to_country)

    for feature in geo_data['features']:
        if 'id' not in feature:
            feature['id'] = feature['properties'].get('iso_a3') or feature['prsoperties'].get('id')

    fig = go.Figure(go.Choroplethmapbox(
        geojson=geo_data,
        locations=df_grouped["iso_code"],
        z=df_grouped["AI Adoption Rate (%)"],
        colorscale='Viridis',
        marker_opacity=0.6,
        marker_line_width=1,
        colorbar=dict(
            title=dict(text="AI Adoption<br>Rate (%)", font=dict(size=12, color=TEXT_COLOR)),
            x=1.008, 
            thickness=35,     
            len=1,          
            xpad=0,           
            ypad=0,          
            outlinewidth=2, 
            outlinecolor="white",
            tickfont=dict(size=9, color=TEXT_COLOR),
        ),            
        customdata=df_grouped["Country"],
        hovertemplate="<b>%{customdata}</b><br>" + 
                    "AI Adoption Rate: %{z:.2f}%<extra></extra>"
    ))
    
    fig.update_layout(
        mapbox_style="carto-positron",
        mapbox_zoom=1.6,
        mapbox_center={"lat": 20, "lon": 10},
        title=None,
        margin=dict(t=0, b=0, l=0, r=0),
        paper_bgcolor='rgba(0,0,0,0)',  # transparent background
        plot_bgcolor='rgba(0,0,0,0)',  # transparent plot background
    )

    
    return fig 


def get_donut_chart(df_country):
    top_tools = df_country["Top AI Tools Used"].value_counts()
    percentages = [v / top_tools.sum() * 100 for v in top_tools.values.tolist()]
    text_labels = [f"{p:.1f}%" if p >= 5 else "" for p in percentages] # Show percentage only if >= 5%

    fig = go.Figure(data=[go.Pie(
        labels=top_tools.index,
        values=top_tools.values,
        hole=0.5,
        text=text_labels,
        textinfo='text',  # only use manual text labels
        textposition='inside',
        insidetextorientation='horizontal',
        marker=dict(line=dict(color='#fff', width=1)),
        showlegend=True,
        hovertemplate="%{label}<br>%{percent:.2%}<extra></extra>"
    )])

    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        paper_bgcolor='rgba(0,0,0,0)',  # transparent background
        plot_bgcolor='rgba(0,0,0,0)',
        annotations=[dict(
            text=f"Top Tools<br>used", 
            x=0.5, y=0.5,
            showarrow=False,
            xanchor='center',
            yanchor='middle',
            align='center',
        )],
        legend=dict(
            orientation="v",       # vertikal
            x=1,                   # Rechts außen
            xanchor="left",
            y=0.5,                 # Vertikal zentriert
            bgcolor="rgba(0,0,0,0)",  # transparent
            font=dict(color=TEXT_COLOR, size=9),
            itemwidth=30,          # KLEINER machen (war standardmäßig 40)
            itemsizing="constant", # Wichtig für konsistente Größe
        ),
        font=dict(color=TEXT_COLOR, size=10),
        hoverlabel=dict(font_size=11),
    )

    return fig


def get_content_bar_chart(df_country):
    df_industry = (
        df_country.groupby("Industry")["AI-Generated Content Volume (TBs per year)"]
        .sum()
        .reset_index()
        .sort_values(by="AI-Generated Content Volume (TBs per year)", ascending=False)
    )

    total_volume = df_industry["AI-Generated Content Volume (TBs per year)"].sum()

    df_industry["Percentage"] = df_industry["AI-Generated Content Volume (TBs per year)"] / total_volume * 100

    fig = px.bar(
        df_industry,
        x="Industry",
        y="Percentage",
        title=f"AI-Generated Content Distribution by Industry",
    )

    fig.update_layout(
        title=dict(
            font=dict(size=11),
            x=0.5,                   # center title
            y=0.95,                   # closer to top
            xanchor='center',
            yanchor='top'
        ),
        margin=dict(l=40, r=10, t=22, b=5),
        autosize=True, 
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_COLOR, size=10),
        hoverlabel=dict(font_size=11),
        bargap=0.1,  
    )

    fig.update_traces(
        marker = dict(
            color="#6d7883",
            line=dict(
                width=1,
                color="#ffffff"
            )
        ),
        hovertemplate="%{x}<br>%{y:.2f}% of total<extra></extra>"
    )

    fig.update_xaxes(
        title=None,             # remove the title "Industry"
        tickangle=30,
        tickfont=dict(size=8),

    )

    fig.update_yaxes(
        title=dict(text="Percentage (%)", font=dict(size=8), standoff=5),
        tickfont=dict(size=8),
        ticksuffix="%",
    )

    return fig


def get_heatmap(df_country):   
    long_labels = [
        "Consumer Trust in AI (%)",
        "Job Loss Due to AI (%)",
        "AI Adoption Rate (%)",
        "Revenue Increase Due to AI (%)",
        "Market Share of AI Companies (%)"
    ]

    short_labels = [
        "Consumer Trust", "Job Loss", "AI Adoption", "Revenue Increase", "Market Share"
    ]

    correlation_matrix = df_country[long_labels].corr()

    # hovertexts need to stay in the long format for clarity
    hover_text = [
        [f"{long_labels[i]} vs {long_labels[j]}: {correlation_matrix.values[i][j]:.3f}"
         for j in range(len(long_labels))]
        for i in range(len(long_labels))
    ]

    # Heatmap-Plot
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=short_labels,  # use short labels for x-axis
        y=short_labels,  # also use short labels for y-axis
        text=hover_text,
        hoverinfo="text", 
        colorscale='Viridis',
        colorbar=dict(
            title='Correlation<br>Coefficient',
            title_font=dict(size=9),
            bgcolor='rgba(0,0,0,0)'
        ),
        zmin=0, zmax=1,
    ))

    # Layout & Achsen
    fig.update_layout(
        title=dict(
            text="Correlation Heatmap of Industry Metrics",
            x=0.5,
            y=0.97,
            xanchor="center",
            font=dict(size=11)
        ),
        margin=dict(t=35, l=10, r=10, b=10),
        xaxis=dict(
            tickangle=45,
            tickfont=dict(size=8, color='white'),
            automargin=True,  
            showgrid=False, # remove grid lines
            zeroline=False, # remove zero line
            showline=False, # remove axis line
            constrain="domain" # ensures x-axis does not extend beyond data
        ),
        yaxis=dict(
            tickfont=dict(size=8, color='white'),
            showgrid=False,
            zeroline=False,
            showline=False,
            scaleanchor="x",  # y-axis scale matches x-axis
            scaleratio=1,     # ensures equal scaling
            automargin=True
        ),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_COLOR, size=8),
        hoverlabel=dict(font_size=10)
    )

    return fig


def get_radar_chart(df_country, selected_industries=None):
    industries = df_country["Industry"].unique() if selected_industries is None else selected_industries
    metrics = ["AI Adoption Rate (%)", "Job Loss Due to AI (%)", "Human-AI Collaboration Rate (%)", "Market Share of AI Companies (%)", "Revenue Increase Due to AI (%)", "Consumer Trust in AI (%)"]

    fig = go.Figure()

    for industry in industries:
        df_industry = df_country[df_country["Industry"] == industry]
        values = [df_industry[metric].mean() for metric in metrics]

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=metrics + [metrics[0]],  # close the radar chart
            customdata=metrics + [metrics[0]],  # für Hover
            fill='none',
            name=industry,
            mode='lines+markers',
            hovertemplate=(
                "Industry: " + industry + "<br>" +
                "Metric: %{customdata}<br>" +
                "Value: %{r}%<extra></extra>"
            ),
        ))

    fig.update_layout(
        polar=dict(
            bgcolor="#2c2c2c",
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickfont=dict(size=8),
                gridcolor="#555",  # Linien zwischen Kreisen
                linecolor="white",  # Kreislinie außen
                showline=True,
                ticks=""
            ),
            angularaxis=dict(
                tickfont=dict(size=9),
                rotation=-30,
                gridcolor="#555",
                linecolor="white",
                showline=True,
                ticks=""
            )
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.75,         
            xanchor="left",
            x=0.90,
            font=dict(color=TEXT_COLOR, size=9),
            itemwidth=40,      
            itemsizing="constant",
            valign="top",
            traceorder="normal",
        ),
        title=dict(
            text=f"Average AI Metrics per Industry (in %)",
            x=0.5,
            xanchor="center",
            y=0.97,
            font=dict(size=11)
        ),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_COLOR, size=10),
        margin=dict(t=45, b=25, l=10, r=10),
        hoverlabel=dict(font_size=11)
    )

    return fig


def get_line_chart(df_country):
    fig = go.Figure()

    # Gruppiere nach Jahr, berechne jeweils den Mittelwert (du kannst hier auch median() verwenden)
    df_grouped = df_country.groupby("Year")[[
        "Consumer Trust in AI (%)",
        "Revenue Increase Due to AI (%)",
        "Job Loss Due to AI (%)",
        "AI Adoption Rate (%)",
        "Human-AI Collaboration Rate (%)",
        "Market Share of AI Companies (%)"
    ]].mean().reset_index()

    selected_metrics = [
        "Consumer Trust in AI (%)",
        "Revenue Increase Due to AI (%)",
        "Job Loss Due to AI (%)",
        "AI Adoption Rate (%)",
        "Human-AI Collaboration Rate (%)",
        "Market Share of AI Companies (%)"
    ]

    short_metrics = [
        "Consumer Trust", "Revenue Increase", "Job Loss", "AI Adoption", "Collaboration Rate", "Market Share"
    ]

    for metric, short_metric in zip(selected_metrics, short_metrics):
        fig.add_trace(go.Scatter(
            x=df_grouped["Year"],
            y=df_grouped[metric],
            mode='lines+markers',
            name=short_metric,
            line=dict(shape='linear'),
            hovertemplate=f"Year: %{{x}}<br>{short_metric}: %{{y:.1f}}%<extra></extra>"
        ))

    # Layout anpassen
    fig.update_layout(
        title=dict(
            text=f"AI Impact Metrics per year from 2020 to {df_country['Year'].max()}",
            x=0.5,
            xanchor="center",
            y=0.95,
            font=dict(size=11)
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=9)
        ),
        yaxis=dict(
            title=dict(
                text="Percentage (%)",
                font=dict(size=9),
                standoff=5  # Abstand zum Rand
            ),
            range=[0, 103],  # mehr Platz nach oben
            tickfont=dict(size=9),
            rangemode="tozero",
            title_font=dict(size=9),
            showgrid=True,            # Gitterlinien aktivieren
            gridcolor="rgba(255,255,255,0.35)",  # Subtile weiße Linien
            tickmode="array",
            tickvals=[0, 25, 50, 75, 100],
            gridwidth=0.5             # Dünnere Linien
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.10,           # weiter nach unten
            xanchor="center",
            x=0.5,
            font=dict(size=9),
            itemwidth=40,      # Breite jedes Eintrags
            itemsizing="constant",
            valign="top",
            traceorder="normal"
        ),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_COLOR, size=10),
        margin=dict(t=35, b=10, l=10, r=20),
        hoverlabel=dict(font_size=11)
    )

    return fig


def strictness_to_label(value):
    if value < 0.33:
        return "Lenient"
    elif value < 0.66:
        return "Moderate"
    else:
        return "Strict"

def label_to_strictness(label):
    if label == "Lenient":
        return 0
    elif label == "Moderate":
        return 0.5
    elif label == "Strict":
        return 1
    else:
        raise ValueError(f"Unknown label: {label}")

def get_gauge(df_country):
    # replace value "strict" by "1", "lenient" by "0", "moderate" by "0.5"
    df_country["Regulation Status"] = df_country["Regulation Status"].replace({
        "Strict": 1,
        "Lenient": 0,
        "Moderate": 0.5
    })
    avg_strictness = df_country["Regulation Status"].mean()

    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=avg_strictness,
        gauge={
            'axis': {
                'range': [0, 1], 
                'tickwidth': 1,
                'tickvals': [0, 1],
                'ticktext': ['Lenient', 'Strict'],
                'tickcolor': TEXT_COLOR
            },
            'bar': {'color': "white", 'thickness': 0.4},
            'borderwidth': 2,
            'steps': [
                {'range': [0.0, 0.333], 'color': '#2ca02c'},   # green
                {'range': [0.333, 0.666], 'color': '#ff7f0e'},   # orange
                {'range': [0.666, 1.0], 'color': '#d62728'},   # red
            ],
            'threshold': {
                'line': {'color': "white", 'width': 3},
                'thickness': 1,
                'value': avg_strictness
            }
        },
        domain={'x': [0, 1], 'y': [0, 1]},
    ))

    fig.add_annotation(
        text=strictness_to_label(avg_strictness),
        font=dict(color=TEXT_COLOR, size=15),
        x=0.5, y=0.05,
        showarrow=False
    )

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # transparent background
        plot_bgcolor="rgba(0,0,0,0)",  # transparent plot background
        font=dict(color=TEXT_COLOR, size=10),
        title=dict(
            text="Average Regulation Strictness",
            font=dict(color=TEXT_COLOR, size=11),
            x=0.5,
            y=1,
            xanchor="center",
            yanchor="top"
        ),
        margin=dict(t=40, b=20, l=50, r=50),
    )

    return fig


def get_total_ai_volume(df_country):
    total_ai_content_tb = df_country["AI-Generated Content Volume (TBs per year)"].sum()

    fig = go.Figure(go.Indicator(
        mode="number",
        value=total_ai_content_tb,
        number={
            "font": {"family": "Segment7, monospace", "color": "#00ffff", "size": 68},
        },
        domain={'x': [0, 1], 'y': [0, 1]}
    ))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",  # transparent background
        plot_bgcolor="rgba(0,0,0,0)",  # transparent plot background
        font=dict(color=TEXT_COLOR, size=10),
        margin=dict(t=30, b=10, l=10, r=10),
        title=dict(
            text="Total AI Content Generated (TBs)",
            font=dict(color=TEXT_COLOR, size=11),
            x=0.5,
            y=1,
            xanchor="center",
            yanchor="top"
        ),
    )

    return fig


def get_bubble_chart(df):
    return html.Div([
        html.Div([
            dcc.Graph(id='bubble-chart'),
            html.Div(["Bubble Size is proportional to the AI-Generated Content Volume"], style={"color": TEXT_COLOR, "fontSize": "12px", "marginLeft": "10px", "textAlign": "center", "marginRight": "100px"}),
        ], style={"width": "100%", "height": EXPLORATIVE_HEIGHT, "marginBottom": "50px"}),

        html.Div([
            html.Div([
                html.Label("X-Axis:", style={"fontSize": EXPLORATIVE_OPTIONS_SIZE, "marginBottom": "5px"}),
                dcc.Dropdown(
                    id='bubble-x-axis',
                    options=[{'label': col, 'value': col} for col in {'Market Share of AI Companies (%)', 'Revenue Increase Due to AI (%)', 'Job Loss Due to AI (%)', 'Human-AI Collaboration Rate (%)', 'Consumer Trust in AI (%)'}],
                    value='Job Loss Due to AI (%)',
                    clearable=False         
                )
            ], style={"width": "100%", "textAlign": "left", "marginBottom": "15px"}),

            html.Div([
                html.Label("Year:", style={"fontSize": EXPLORATIVE_OPTIONS_SIZE, "marginBottom": "5px"}),
                dcc.Slider(
                    id='year-slider',
                    min=df["Year"].min()-1,
                    max=df["Year"].max(),
                    step=1,
                    value=2023,
                    marks={
                        year: {
                            'label': marks_slider[year]["label"],
                            'style': {
                                'color': TEXT_COLOR,
                                'fontSize': EXPLORATIVE_LEGEND_TITLE_SIZE,
                                'fontWeight': 'standard'
                            }
                        } for year in marks_slider
                    },
                    tooltip=None,
                    included=True,
                    updatemode='mouseup',  # Aktualisiere nur nach Loslassen
                )
            ], style={"width": "100%", "textAlign": "left"})
        ], style={"display": "block", "width": "96%", "marginLeft": "auto", "marginRight": "auto", "marginBottom": "10px"}),
    ])


def get_big_line_chart():
    return html.Div([
        html.Div([
            dcc.Graph(id='big-line-chart')
        ], style={"width": "100%", "height": EXPLORATIVE_HEIGHT, "marginBottom": "50px"}),

        html.Div([
            html.Div([
                html.Label("Filter Options", style={"fontSize": EXPLORATIVE_OPTIONS_SIZE, "marginBottom": "5px"}),
                dcc.Dropdown(
                    id='filter-line-chart',
                    options=[],
                    value=None,
                    clearable=True,
                    placeholder="Select a filter"
                )
            ], id="filter-line-chart-container", style={"width": "33%", "paddingRight": "10px"}),

            html.Div([
                html.Label("Group", style={"fontSize": EXPLORATIVE_OPTIONS_SIZE, "marginBottom": "5px"}),
                dcc.Dropdown(
                    id='group-line-chart',
                    options=[{'label': col, 'value': col} for col in {'Metrics', 'Industry', 'Country', 'Regulation Status', 'Generated Content Volume'}],
                    value='Metrics',
                    clearable=False
                )
            ], id="group-line-chart-container", style={"width": "33%", "paddingRight": "10px"}),

            html.Div([
                html.Label("Select Metric", style={"fontSize": EXPLORATIVE_OPTIONS_SIZE, "marginBottom": "5px"}),
                dcc.Dropdown(
                    id='select-metric-dropdown',
                    options=[{'label': col, 'value': col} for col in {'Consumer Trust in AI (%)', 'Revenue Increase Due to AI (%)', 'Job Loss Due to AI (%)', 'AI Adoption Rate (%)', 'Human-AI Collaboration Rate (%)', 'Market Share of AI Companies (%)', 'AI-Generated Content Volume (TBs per year)'}],
                    value='AI Adoption Rate (%)',
                    clearable=False,
                    style={"fontSize": "11px"}
                )
            ], id="select-metric-container", style={"width": "33%"}),
        ], style={"display": "flex", "width": "96%", "marginBottom": "10px", "marginLeft": "auto", "marginRight": "auto"}),

        html.Div([
                dcc.Dropdown(
                    id='metric-dropdown',
                    options=[],
                    value=None,
                    multi=True,
                    placeholder="Select Metrics",   
                ),
                html.Button(
                    "All", 
                    id="select-all-button", 
                    n_clicks=0,
                    style={"width": "100%", "display": "flex", "alignItems": "center", "justifyContent": "center"}
                )
        ], id='metric-dropdown-container', style= {'display': 'block', 'width': '96%', 'color': 'black'}),
    ])


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # src/ai_dataset/ -> src/ -> project root
data_file = project_root / "data" / "Global_AI_Content_Impact_Dataset.csv"

df = pd.read_csv(data_file)
df["iso_code"] = df["Country"].apply(name_to_iso3)
df["Regulation Status Int"] = df["Regulation Status"].replace({
    "Strict": 1,
    "Lenient": 0,
    "Moderate": 0.5
})

choropleth_map = get_choropleth_map()
MAP_STYLE = {"height": "70vh", "margin": "5px 40px 0 40px"}

all_years = int(df["Year"].min()-1)
marks_slider = {all_years: {"label": "All"}}
marks_slider.update({int(y): {"label": str(y)} for y in sorted(df["Year"].unique())})

# Layout
app.layout = html.Div([
    dcc.Store(id='selected-country', data=None),

    # choropleth map
    html.Div(id="map-area"),

    # deeper analysis area
    html.Div([
        html.Div(get_bubble_chart(df), style={"gridArea": "a", "background": BACKGROUND_COLOR, "color": TEXT_COLOR}),
        html.Div(get_big_line_chart(), style={"gridArea": "b", "background": BACKGROUND_COLOR, "color": TEXT_COLOR})
    ], style={
        "display": "grid",
        "gridTemplateAreas": """
            'a b'
        """,
        "gridTemplateColumns": "8fr 7fr",
        "height": "80vh",
        "gap": "10px",
        "margin": "30px 40px",
    })
], style={
    "backgroundColor": BASE_COLOR,
    "color": TEXT_COLOR,
    "padding": "0",
    "margin": "0",
    "width": "100%",
    "position": "absolute",
    "top": 0,
    "left": 0,
    }
)

# show analysis content based on selected country
@callback(
    Output('map-area', 'children'),
    Input('selected-country', 'data'),
)
def render_content(selected_country):
    if selected_country is None:
        return html.Div(id="map-area", children=[
            dcc.Markdown(f"Average AI Adoption Rate per Country (2020-2025)", style={"color": TEXT_COLOR, "margin": "10px 40px 0 40px", "fontSize": CHOROPLETH_TITLE_SIZE}),
            dcc.Graph(id="choropleth-map", figure=choropleth_map, style=MAP_STYLE)
        ])
    else:
        df_country = df[df["iso_code"] == selected_country]
        
        return html.Div([
            dcc.Markdown(f"Detailed Analysis for {df_country['Country'].iloc[0]} (2020 – {df_country["Year"].max()})", style={"color": TEXT_COLOR, "margin": "10px 40px 0 40px", "fontSize": CHOROPLETH_TITLE_SIZE}),

            html.Div([
                html.Div([
                    html.Div(
                        dcc.Graph(figure=get_donut_chart(df_country), config={"displayModeBar": False}, style={"width": "100%", "height": "100%"}),
                        style={"gridArea": "a", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                    ),

                    html.Div(
                        dcc.Graph(figure=get_content_bar_chart(df_country), config={"displayModeBar": False}, style={"width": "100%", "height": "100%"}), 
                        style={"gridArea": "b", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                    ),

                    html.Div(
                        dcc.Graph(figure=get_heatmap(df_country), config={"displayModeBar": False}, style={"width": "100%", "height": "100%"}),
                        style={"gridArea": "c", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                    ),

                    html.Div(
                        dcc.Graph(figure=get_radar_chart(df_country), config={"displayModeBar": False}, style={"width": "100%", "height": "100%"}),
                        style={"gridArea": "d", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                    ),

                    html.Div(
                        dcc.Graph(figure=get_line_chart(df_country), config={"displayModeBar": False}, style={"width": "100%", "height": "100%"}),
                        style={"gridArea": "e", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}                       
                    ),

                    html.Div(
                        html.Button("Back to Map", id="back-button"),
                        style={"gridArea": "f", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR, "padding": "10px", "textAlign": "center"}
                    ),

                    html.Div([
                        # Gauge oben
                        html.Div(
                            dcc.Graph(figure=get_gauge(df_country), config={"displayModeBar": False},
                                    style={"width": "100%", "height": "100%"}),
                            style={"flex": "1", "padding": "10px", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                        ),
                        html.Hr(style={
                            "borderTop": f"10px solid {BASE_COLOR}",
                            "margin": "0 0"
                        }),
                        # Zahl unten
                        html.Div(
                            dcc.Graph(figure=get_total_ai_volume(df_country), config={"displayModeBar": False},
                                    style={"width": "100%", "height": "100%"}),
                            style={"flex": "1", "padding": "10px", "backgroundColor": BACKGROUND_COLOR, "color": TEXT_COLOR}
                        )
                    ],
                    style={
                        "display": "flex",
                        "flexDirection": "column",
                        "justifyContent": "space-between",
                        "height": "100%",
                        "width": "100%",
                        "gridArea": "g",
                        "color": TEXT_COLOR,
                        "backgroundColor": BACKGROUND_COLOR
                    }
                )
                ], style={
                    "display": "grid",
                    "gridTemplateAreas": """
                        'a b c g'
                        'd d c g'
                        'd d e e'
                        'd d e e'
                        'f f e e'
                    """,
                    "gridTemplateColumns": "3fr 5fr 4fr 3fr",
                    "gridTemplateRows": "5fr 6fr 3fr 3fr 1fr",
                    "height": "70vh",
                    "gap": "10px",
                    "margin": "5px 40px 0 40px",
                    }),
            ]),
        ])

# callback to change between map and country analysis
@callback(
    Output('selected-country', 'data'),
    [Input('choropleth-map', 'clickData')],
    prevent_initial_call=True
)
def update_from_map_click(clickData):
    if clickData:
        return clickData['points'][0]['location']
    raise dash.exceptions.PreventUpdate

# callback for the back button to reset the view
@callback(
    Output('selected-country', 'data', allow_duplicate=True),
    [Input('back-button', 'n_clicks')],
    prevent_initial_call=True
)
def reset_view(n_clicks):
    if n_clicks and n_clicks > 0:
        return None
    raise dash.exceptions.PreventUpdate


@callback(
    Output('bubble-chart', 'figure'),
    Input('bubble-x-axis', 'value'),
    Input('year-slider', 'value')
)
def update_bubble_chart(x, year):    
    filtered_df = df if year == df["Year"].min()-1 else df[df['Year'] == year]
    display_year = "2020 - 2025" if year == df["Year"].min()-1 else year

    if year == df["Year"].min()-1:
        filtered_df = filtered_df.groupby(["Country", "Industry"]).mean(numeric_only=True).reset_index()
        filtered_df["Regulation Status Mean"] = filtered_df["Regulation Status Int"].map(strictness_to_label)

    regulation_status_column = 'Regulation Status' if year != df["Year"].min()-1 else 'Regulation Status Mean'


    fig = px.scatter(
        filtered_df,
        x=x,
        y='AI Adoption Rate (%)',
        size='AI-Generated Content Volume (TBs per year)',
        color=regulation_status_column, 
        hover_name='Country',
        size_max=40,
        template='plotly_dark',
        custom_data=['Industry', regulation_status_column, 'Year']
    )

    fig.update_traces(
        hovertemplate="<b>%{hovertext}</b><br><br>" +
                  f"{x}: %{{x:.1f}}%<br>" +
                  "AI Adoption: %{y:.1f}%<br>" +
                  "Content Volume: %{marker.size:.1f} TBs<br>" +
                  "Industry: %{customdata[0]}<br>" +
                  "Regulation: %{customdata[1]}<extra></extra>",
    )

    fig.update_layout(
        title=dict(
            text=f"What impact does the increased use of AI have? ({display_year})",
            x=0.5,
            xanchor="center",
            y=0.98,
            font=dict(size=EXPLORATIVE_TITLE_SIZE)
        ),
        xaxis=dict(
            tickfont=dict(size=EXPLORATIVE_TICK_SIZE),
            tickmode="array",
            title=dict(
                font=dict(size=EXPLORATIVE_AXIS_LABEL_SIZE),
                standoff=10,  # Abstand zum Rand
            ),
        ),
        yaxis=dict(
            title=dict(
                font=dict(size=EXPLORATIVE_AXIS_LABEL_SIZE),
                standoff=5,  # Abstand zum Rand
            ),
            tickfont=dict(size=EXPLORATIVE_TICK_SIZE),
            rangemode="tozero",
            showgrid=True,            # Gitterlinien aktivieren
            gridcolor="rgba(255,255,255,0.35)",  # Subtile weiße Linien
            tickmode="array",
            gridwidth=0.5             # Dünnere Linien
        ),
        legend=dict(
            orientation="v",
            yanchor="top",
            xanchor="left",
            x=1.01,
            itemwidth=30,      # Breite jedes Eintrags
            itemsizing="trace",
            valign="top",
            traceorder="normal",
            title=dict(
                font=dict(size=EXPLORATIVE_LEGEND_TITLE_SIZE),
                side="top"  # Title above legend items
            ),
            font=dict(
                color=TEXT_COLOR,
                size=EXPLORATIVE_LEGEND_FONT_SIZE
            )
        ),
        margin=dict(t=35, b=10, l=20, r=20),
        paper_bgcolor='rgba(0,0,0,0)',  # transparent background
        plot_bgcolor='rgba(0,0,0,0)',  # transparent plot 
        hoverlabel=dict(font_size=EXPLORATIVE_HOVER_SIZE)
    )

    return fig


def apply_filter(df, filter_value, selected_metrics):
    return df[df[filter_value].isin(selected_metrics)]

@callback(
    Output('big-line-chart', 'figure'),
    Input('group-line-chart', 'value'),
    Input('filter-line-chart', 'value'),
    Input('metric-dropdown', 'value'),
    Input('select-metric-dropdown', 'value')
)
def update_big_line_chart(selected_group, filter_value, filtered_selected_metrics, select_metric):    
    fig = go.Figure()

    all_metrics = [
        "Consumer Trust in AI (%)",
        "Revenue Increase Due to AI (%)",
        "Job Loss Due to AI (%)",
        "AI Adoption Rate (%)",
        "Human-AI Collaboration Rate (%)",
        "Market Share of AI Companies (%)"
    ]

    df_filtered = df.copy()
    if filter_value is not None:
        df_filtered = apply_filter(df_filtered, filter_value, filtered_selected_metrics)
    
    if selected_group == "Metrics":
        select_metric = None
        df_grouped = df_filtered.groupby("Year").mean(numeric_only=True).reset_index()

        for metric in all_metrics:
            if metric in df_grouped.columns:
                fig.add_trace(go.Scatter(
                    x=df_grouped["Year"],
                    y=df_grouped[metric],
                    mode="lines+markers",
                    name=metric,
                    hovertemplate=f"{metric}: %{{y:.2f}}<br>Jahr: %{{x}}<extra></extra>"
                ))
    elif selected_group == 'Generated Content Volume':
        select_metric = None
        df_grouped = df_filtered.groupby("Year")["AI-Generated Content Volume (TBs per year)"].sum().reset_index()
        
        # add trace for AI-Generated Content Volume
        fig.add_trace(go.Scatter(
            x=df_grouped["Year"],
            y=df_grouped["AI-Generated Content Volume (TBs per year)"],
            mode="lines+markers",
            name="Content Volume (TBs)",
            hovertemplate="Content Volume: %{y:.2f} TB<br>Jahr: %{x}<extra></extra>"
        ))
    else:
        if select_metric == 'AI-Generated Content Volume (TBs per year)':
            df_grouped = df_filtered.groupby(["Year", selected_group])[select_metric].sum().reset_index()
        else:
            df_grouped = df_filtered.groupby(["Year", selected_group]).mean(numeric_only=True).reset_index()
        
        for group_val in df_grouped[selected_group].unique():
            df_subset = df_grouped[df_grouped[selected_group] == group_val]
            fig.add_trace(go.Scatter(
                x=df_subset["Year"],
                y=df_subset[select_metric],
                mode="lines+markers",
                name=str(group_val),
                hovertemplate=f"{select_metric}: %{{y:.2f}}<br>{selected_group}: {group_val}<br>Jahr: %{{x}}<extra></extra>"
            ))

    if selected_group != 'Metrics' and selected_group != 'Generated Content Volume':
        title_text = f"{select_metric} by {selected_group} over Time (2020 - 2025)"
    elif selected_group == 'Generated Content Volume':
        title_text = "AI-Generated Content Volume over Time (2020 - 2025)"
    else:
        title_text = "AI-Metrics over Time (2020 - 2025)"

    max_value = df_grouped["AI-Generated Content Volume (TBs per year)"].max() if selected_group == 'Generated Content Volume' or select_metric == 'AI-Generated Content Volume (TBs per year)' else 100

    if isnan(max_value):
        max_value = 0

    fig.update_layout(
        title=dict(
            text=title_text,
            x=0.5,
            xanchor="center",
            y=0.98,
            font=dict(size=EXPLORATIVE_TITLE_SIZE)
        ),
        xaxis=dict(
            title=None,
            tickfont=dict(size=EXPLORATIVE_TICK_SIZE),
            # show range always from 2020 to 2025
            range=[2020, 2025],
            tickmode="array",
            tickvals=list(range(2020, 2026))
        ),
        yaxis=dict(
            title=dict(
                text="Percentage (%)" if selected_group != 'Generated Content Volume' and select_metric != 'AI-Generated Content Volume (TBs per year)' else "Content Volume (TBs)",
                font=dict(size=EXPLORATIVE_AXIS_LABEL_SIZE),
                standoff=5,  # Abstand zum Rand
            ),
            range=[0, max_value * 1.03],  # mehr Platz nach oben
            tickfont=dict(size=EXPLORATIVE_TICK_SIZE),
            rangemode="tozero",
            showgrid=True,            # Gitterlinien aktivieren
            gridcolor="rgba(255,255,255,0.35)",  # Subtile weiße Linien
            tickmode="array",
            tickvals=[0, int(max_value*0.25), int(max_value*0.5), int(max_value*0.75), ceil(max_value)],
            gridwidth=0.5,             # Dünnere Linien
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.075,           # weiter nach unten
            xanchor="center",
            x=0.5,
            font=dict(size=EXPLORATIVE_LEGEND_FONT_SIZE),
            itemwidth=50,      # Breite jedes Eintrags
            itemsizing="constant",
            valign="top",
            traceorder="normal",
        ),
        paper_bgcolor='rgba(0,0,0,0)', 
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color=TEXT_COLOR, size=10),
        margin=dict(t=35, b=10, l=10, r=20),
        hoverlabel=dict(font_size=EXPLORATIVE_HOVER_SIZE)
    )

    return fig

@callback(
    [Output('filter-line-chart', 'options'),
     Output('filter-line-chart', 'value')],
    Input('group-line-chart', 'value')
)
def update_filter_options(selected_group):
    options = [
        'Industry',
        'Country',
        'Regulation Status',
    ]
    if selected_group in options:
        options.remove(selected_group)
    
    default_value = None
    
    return options, default_value


@callback(
    [Output('metric-dropdown', 'options'),
     Output('metric-dropdown', 'value')],
    Input('filter-line-chart', 'value'),
)  
def update_applied_filter_line_chart(selected_group):
    if selected_group == 'Metrics':
        options = [
            {'label': 'Consumer Trust in AI (%)', 'value': 'Consumer Trust in AI (%)'},
            {'label': 'Job Loss Due to AI (%)', 'value': 'Job Loss Due to AI (%)'},
            {'label': 'AI Adoption Rate (%)', 'value': 'AI Adoption Rate (%)'},
            {'label': 'Revenue Increase Due to AI (%)', 'value': 'Revenue Increase Due to AI (%)'},
            {'label': 'Human-AI Collaboration Rate (%)', 'value': 'Human-AI Collaboration Rate (%)'},
            {'label': 'Market Share of AI Companies (%)', 'value': 'Market Share of AI Companies (%)'}
        ]
        default_value = ['Consumer Trust in AI (%)', 'Job Loss Due to AI (%)', 'AI Adoption Rate (%)', 'Revenue Increase Due to AI (%)', 'Human-AI Collaboration Rate (%)', 'Market Share of AI Companies (%)']
    elif selected_group == 'Industry':
        options = [{'label': industry, 'value': industry} for industry in df['Industry'].unique()]
        default_value = [industry for industry in df['Industry'].unique()]
    elif selected_group == 'Country':
        options = [{'label': country, 'value': country} for country in df['Country'].unique()]
        default_value = [country for country in df['Country'].unique()]
    elif selected_group == 'Regulation Status':
        options = [
            {'label': 'Strict', 'value': 'Strict'},
            {'label': 'Moderate', 'value': 'Moderate'},
            {'label': 'Lenient', 'value': 'Lenient'}
        ]
        default_value = ['Strict', 'Moderate', 'Lenient']
    elif selected_group == 'Generated Content Volume':
        options = [{'label': 'AI-Generated Content Volume (TBs per year)', 'value': 'AI-Generated Content Volume (TBs per year)'}]
        default_value = ['AI-Generated Content Volume (TBs per year)']
    else:
        options = []
        default_value = None
    
    return options, default_value


@callback(
    Output('metric-dropdown-container', 'style'),
    Input('filter-line-chart', 'value')
)
def toggle_metric_dropdown_visibility(filter_value):
    if filter_value is None:
        return {'display': 'none'}  # hide Dropdown
    else:
        return {'display': 'block', 'width': '96%', 'marginLeft': "auto", "marginRight": "auto", 'color': 'black'}  # show Dropdown


@callback(
    [Output('filter-line-chart-container', 'style'),
     Output('group-line-chart-container', 'style'),
     Output('select-metric-container', 'style'),],
    Input('group-line-chart', 'value')
)
def toggle_select_metric_container_visibility(selected_group):
    if selected_group != 'Metrics' and selected_group != 'Generated Content Volume':
        return {"width": "33%", "paddingRight": "10px"}, {"width": "33%", "paddingRight": "10px"}, {"width": "33%"}
    else:
        return {"width": "50%", "paddingRight": "10px"}, {"width": "50%"}, {'display': 'none'}
    

@callback(
    Output('metric-dropdown', 'value', allow_duplicate=True),
    Input('select-all-button', 'n_clicks'),
    State('metric-dropdown', 'options'),
    State('metric-dropdown', 'value'),
    prevent_initial_call=True
)
def toggle_select_all(n_clicks, options, current_values):
    all_values = [o['value'] for o in options]
    if set(current_values) == set(all_values):
        return []  # alles abwählen
    return all_values  # alles auswählen

if __name__ == "__main__":
    app.run(debug=True)
