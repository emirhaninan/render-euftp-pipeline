import os
import pandas as pd
import datetime as dt
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output

def run():
    # Find file relative to app location
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, "Researcher_Assigned_Calls_With_Deadline_URL.xlsx")

    # Read in Excel
    data = pd.read_excel(file_path)

    # Convert 'Deadline' column to datetime and filter out past deadlines
    data['Deadline'] = pd.to_datetime(data['Deadline'], format='%d %m %Y').dt.date
    today = dt.date.today()
    data_filtered = data[data['Deadline'] >= today]  # Filter out past deadlines
    data_filtered = data_filtered.sort_values(by='Deadline').reset_index(drop=True)

    # Function to assign row color based on deadline
    def assign_color(deadline_date, today=today):
        days_until_deadline = (deadline_date - today).days
        if days_until_deadline <= 10:
            return 'red'  # Urgent
        elif days_until_deadline <= 30:
            return 'yellow'  # Close
        else:
            return 'green'  # Plenty of time

    data_filtered['Row_Color'] = data_filtered['Deadline'].apply(assign_color)
    data_filtered['URL'] = data_filtered['URL'].apply(lambda x: f"[Link]({x})")
    data_filtered['Formatted_Deadline'] = data_filtered['Deadline'].apply(lambda x: x.strftime('%d-%m-%Y'))

    app = Dash(__name__)

    style_conditions = [
        {
            'if': {'filter_query': '{Row_Color} = "red"'},
            'backgroundColor': 'tomato',
            'color': 'white'
        },
        {
            'if': {'filter_query': '{Row_Color} = "yellow"'},
            'backgroundColor': 'gold',
            'color': 'black'
        },
        {
            'if': {'filter_query': '{Row_Color} = "green"'},
            'backgroundColor': 'lightgreen',
            'color': 'black'
        }
    ]

    # App layout
    app.layout = html.Div([
        html.Div([
            html.H1("Funding Calls Dashboard", style={
                'text-align': 'center', 'color': '#2E4053', 'padding': '10px',
                'font-family': 'Arial, sans-serif', 'text-shadow': '1px 1px 2px #000',
                'margin-top': '20px', 'border': 'none', 'box-shadow': 'none'
            }),

            html.Div([
                dcc.Input(
                    id='professor-search',
                    type='text',
                    placeholder="🔍 Enter Name",
                    style={'width': '100%', 'max-width': '600px', 'padding': '10px',
                           'border': '2px solid #ccc', 'border-radius': '12px',
                           'box-shadow': '0px 4px 8px rgba(0,0,0,0.2)', 'font-size': '16px',
                           'margin': '10px auto'}
                ),
            ], style={'display': 'flex', 'justify-content': 'center', 'padding-bottom': '20px'}),

            html.Div([
                dash_table.DataTable(
                    id='calls-table',
                    columns=[
                        {'name': 'Researcher', 'id': 'Full Name'},
                        {'name': 'Project Name', 'id': 'Assigned Call'},
                        {'name': 'Deadline', 'id': 'Formatted_Deadline'},
                        {'name': 'URL', 'id': 'URL', 'presentation': 'markdown'},
                    ],
                    data=data_filtered.to_dict('records'),
                    style_data_conditional=style_conditions,
                    style_table={
                        'width': '100%',
                        'max-width': '1200px',
                        'margin': '0 auto',
                        'border-radius': '12px',
                        'overflow': 'hidden'
                    },
                    style_cell={
                        'textAlign': 'center',
                        'padding': '15px',
                        'font-family': 'Arial, sans-serif',
                        'border': '1px solid #ddd',
                        'whiteSpace': 'normal',
                        'height': 'auto',
                        'minWidth': '130px'
                    },
                    style_header={
                        'backgroundColor': 'rgba(46, 64, 83, 0.8)',
                        'fontWeight': 'bold',
                        'color': 'white',
                        'text-align': 'center',
                        'border': '1px solid #2E4053'
                    },
                    markdown_options={'link_target': '_blank'}
                )
            ], style={
                'margin': '20px auto',
                'width': '90%',
                'max-width': '1200px',
                'padding': '37px',
                'border-radius': '12px',
                'background-color': 'rgba(255, 255, 255, 0.8)',
                'box-shadow': '0px 8px 16px rgba(0,0,0,0.2)'
            })
        ])
    ], style={
        'display': 'flex',
        'justify-content': 'center',
        'align-items': 'center',
        'flex-direction': 'column',
        'background-image': 'url("/assets/background.jpg")',
        'background-size': 'cover',
        'background-position': 'center',
        'background-attachment': 'fixed',
        'padding-top': '60px',
        'padding-bottom': '60px',
        'width': '100vw',
        'min-height': '100vh',
        'box-sizing': 'border-box',
        'overflow': 'auto'
    })

    @app.callback(
        Output('calls-table', 'data'),
        Input('professor-search', 'value')
    )
    def update_table(professor_name):
        if professor_name:
            filtered_data = data_filtered[data_filtered['Full Name'].str.contains(professor_name, case=False, na=False)]
        else:
            filtered_data = data_filtered
        return filtered_data.to_dict('records')

    port = int(os.environ.get('PORT', 8500))
    app.run(debug=False, host='0.0.0.0', port=port)

# Allows run as script OR via main.py import
if __name__ == '__main__':
    run()
