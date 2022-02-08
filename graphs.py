import pandas as pd
import plotly.express as px
import plotly
import plotly.graph_objects as go
from typing import Optional, List
import re
import numpy as np
import chart_studio.plotly as py
from math import isclose, sqrt


class DataAnalyzer:

    large_rockwell_template = dict(
        layout=go.Layout(title_font=dict(family="Hevletica", size=24))
    )
    color_palette = list(reversed(['rgb(132,29,22)', 'rgb(179,39,39)', 'rgb(222,46,37)', 'rgb(244,81,28)',
                                   'rgb(215,116,102)', 'rgb(252,156,124)',
                                   'rgb(243,210,143)',
                                   'rgb(60,54,50)', 'rgb(99,99,99)', 'rgb(153,153,153)', 'rgb(211,211,211)']))
    color_palette2 = ['rgb(151,144,139)', 'rgb(60,54,50)', 'rgb(243,210,143)',
                      'rgb(222,46,37)', 'rgb(132,29,22)']
    color_pallete3 = ['rgb(153,153,153)', 'rgb(222,46,37)']

    def __init__(self, data: pd.DataFrame):
        self.df = data

    @staticmethod
    def read_data(data: str) -> pd.DataFrame:
        df = pd.read_csv(data)
        return df

    def show_data(self) -> pd.DataFrame:
        return self.df

    def capitalize_list(self, l):
        return [i.capitalize() for i in l]

    def error_gen(self, actual: float, rounded: float):
        divisor = sqrt(1.0 if actual < 1.0 else actual)
        return abs(rounded - actual) ** 2 / divisor

    def round_to_100(self, percents: List[float]):
        if not isclose(sum(percents), 100):
            raise ValueError
        n = len(percents)
        rounded = [int(x) for x in percents]
        up_count = 100 - sum(rounded)
        errors = [(self.error_gen(percents[i], rounded[i] + 1) -
                   self.error_gen(percents[i], rounded[i]), i) for i in range(n)]
        rank = sorted(errors)
        for i in range(up_count):
            rounded[rank[i][1]] += 1
        return rounded

    def create_bar_graph(self, column: str, title: Optional[bool] = False,
                         order: Optional[List[str]] = None,
                         x: Optional[str] = None, y: Optional[str] = None,
                         one_color: bool = False):
        df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(
            normalize=True))
        df_temp[column] = np.array(self.round_to_100(np.array(df_temp[column] * 100))) / 100
        if order:
            not_in_df = [index for index in order if index not in set(list(
                df_temp.index))]
            for i in not_in_df:
                df_temp.loc[i, :] = [np.nan] * len(df_temp.columns)
            df_temp = df_temp.loc[order, ]
        df_temp = df_temp.fillna(0).reset_index()
        return self.plot_bar(df_temp['index'], df_temp[column],
                      title=self.df.loc[0, column] if title else None,
                      x_title=x, y_title=y, one_color=one_color)

    def create_bar_graph_group(self, columns: List[str], title: Optional[bool] = False,
                               order: List[str] = None,
                               x_title: Optional[str] = None, y_title: Optional[str] = None,
                               one_color: bool = False, w: int = 1, names: Optional[List[str]] = None,
                               color_palette: int = 1):
        list_vals = [self.df.loc[0, column] for column in columns]
        for ind, val in enumerate(list_vals):
            if len(val) >= 18:
                list_vals[ind] = list_vals[ind].replace(val,
                                                        re.sub('(' + '\s\S*?' * w + ')\s',
                                                               r'\1<br> ',
                                                               val))
        fig = go.Figure()
        palette = self.color_palette if color_palette == 1 else self.color_palette2
        dict_nums = {}
        for index, response in enumerate(order):
            list_num = []
            for column in columns:
                df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(
                    normalize=True))
                if not response in df_temp.index:
                    list_num.append(0)
                else:
                    list_num.append(df_temp.loc[response, column])
            dict_nums[response] = (index, list_num)
        for val in range(len(list_vals)):
            percentages = []
            for key in dict_nums.keys():
                percentages.append(dict_nums[key][1][val])
            percentages = np.array(self.round_to_100(np.array(percentages) * 100)) / 100
            for ind, key in enumerate(list(dict_nums.keys())):
                dict_nums[key][1][val] = percentages[ind]
        for index, response in enumerate(order):
            fig.add_trace(go.Bar(x=list_vals,
                                 y=[round(i, 1) for i in dict_nums[response][1]],
                                 name=names[index] if names else response,
                                 marker_color=palette[dict_nums[response][0]],
                                 texttemplate='%{y}', textposition='outside',
                                 textfont_size=40
                                 ))
        fig.update_layout(
            font_family='Arial',
            title=title if title else '',
            xaxis_tickfont_size=40,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=40,
                tickfont_size=40

            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=40,
                tickfont_size=40,
                tickformat="1%"
            ),
            bargap=0.15,
            template=self.large_rockwell_template,
            legend=dict(font_size=40, font_family='Arial'),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.write_image("fig.png", height=1300, width=3000, scale=8)
        return fig

    def create_chart_for_categories(self, column: str, title: Optional[bool] = False,
                                    order: Optional[List[str]] = None,
                                    x: Optional[str] = None, y: Optional[str] = None,
                                    one_color: bool = False, sep: str = ',', w = 1):
        temp_df = self.df.copy()
        temp_df.loc[1:, column] = [re.split(sep, str(i)) for i in temp_df.loc[1:, column]]
        df_res = pd.DataFrame(columns=['count'])
        for index_row, tag_list in enumerate(temp_df.loc[1:, column]):
            for index_tag, tag in enumerate(tag_list):
                if len(tag) == 1:
                    temp_df.loc[index_row + 1, column][index_tag + 1] = tag + \
                                                                        temp_df.loc[index_row + 1, column][index_tag + 1]
                    continue
                tag = tag.strip()
                if tag[-1] == '.':
                    tag = tag[:-1]
                if tag in list(df_res.index):
                    df_res.loc[tag, 'count'] += 1
                else:
                    df_res.loc[tag, 'count'] = 1
        for string in order:
            if not string in df_res.index:
                df_res.loc[string, 'count'] = 0
        df_res = df_res.reset_index()
        df_res = df_res[df_res['index'] != 'nan']
        df_res['count'] = [i / sum(df_res['count']) for i in df_res['count']]
        df_res['count'] = np.array(self.round_to_100(np.array(df_res['count'] * 100))) / 100
        for tag in df_res['index']:
            if len(tag) >= 18:
                df_res['index'] = df_res['index'].replace(tag,
                                                          re.sub('(' + '\s\S*?' * w + ')\s',
                                                                 r'\1<br> ',
                                                                 tag))
        self.plot_bar(df_res['index'], df_res['count'],
                      title=column if title else None,
                      x_title=x, y_title=y, one_color=one_color)

    def plot_self_assessment(self, w=2):
        fig = go.Figure()
        df = self.df
        df = df.set_index('Time')
        palette = self.color_pallete3
        x = list(df.columns)
        x = self.capitalize_list(x)
        for ind, val in enumerate(x):
            if len(val) >= 18:
                x[ind] = x[ind].replace(val, re.sub('(' + '\s\S*?' * w + ')\s',
                                                    r'\1<br> ',
                                                    val))
        for index, response in enumerate(['Pre-semester',
                                          'Post-semester']):
            fig.add_trace(go.Bar(x=x,
                                 y=[round(i, 1) for i in df.loc[response, :]],
                                 name=response,
                                 marker_color=palette[-index],
                                 texttemplate='%{y}', textposition='outside'
                                 ))
        fig.update_layout(
            font_family='Arial',
            title='',
            xaxis_tickfont_size=14,
            xaxis=dict(
                title='',
                titlefont_size=20,
                tickfont_size=13,
            ),
            yaxis=dict(
                title='',
                titlefont_size=20,
                tickfont_size=12,
                tickformat = '~%'
            ),
            bargap=0.3,
            template=self.large_rockwell_template
        )
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.48,
            font = dict(size = 16, color = "black")
        ))
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.show()

        fig.write_image("fig.png", height=550, width=900, scale=10)

    def plot_bar(self, x: pd.Series, y: pd.Series, title: Optional[str] = None,
                 x_title: Optional[str] = None,
                 y_title: Optional[str] = None,
                 one_color: bool = False, grouped_bar: bool = False):
        fig = go.Figure()
        x = self.capitalize_list(x)
        if one_color:
            fig.add_trace(go.Bar(x=[str(xs) + '‏‏‎ ‎' for xs in x],
                                 y=[round(i, 1) for i in y],
                                 marker_color='rgb(224,44,36)',
                                 texttemplate='%{y}', textposition='outside',
                                 ))
        else:
            fig.add_trace(go.Bar(x=x,
                                 y=[round(i, 1) for i in y],
                                 marker_color=self.color_palette[:len(x)],
                                 texttemplate='%{y}', textposition='outside'
                                 ))

        fig.update_layout(
            font_family='Hevletica Neue',
            xaxis_tickfont_size=14,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=16,
                tickfont_size=12,
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=16,
                tickfont_size=12,
                tickformat = '1%'
            ),
            bargap=0.15, # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        #fig.write_image("fig.png", height=550, width=900, scale=10)
        fig.update_layout(width=900, height=550, plot_bgcolor='rgba(0,0,0,0)')
        return fig

    def create_pie_chart(self, column: str):
        dictionary = dict(self.df.loc[1:, column].dropna().value_counts())
        fig = go.Figure(data=[go.Pie(labels=list(dictionary.keys()), values=list(dictionary.values()),
                                     marker_colors=['rgb(132,29,22)', 'rgb(243,210,143)'])])
        fig.show()

    def create_gauge_graph(self, column: str):
        promoters = (self.df.loc[1:, column] == 'Promoter').sum() / (len(self.df) - 1)
        detractors = (self.df.loc[1:, column] == 'Detractor').sum() / (len(self.df) - 1)
        fig = go.Figure(go.Indicator(
            font_family='Hevletica Neue',
            mode = "gauge+number",
            value = round(100 * (promoters - detractors), 1),
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {'axis': {'range': [-100, 100]},
                     'bar': {'color': 'rgb(224,44,36)', 'thickness': 1}},))

        fig.show()

    def create_horizontal_bar_graph(self, column: str, order: Optional[List[str]] = None):
        df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(
            normalize=True))
        df_temp[column] = np.array(self.round_to_100(np.array(df_temp[column] * 100)))
        if order:
            not_in_df = [index for index in order if index not in set(list(
                df_temp.index))]
            for i in not_in_df:
                df_temp.loc[i, :] = [np.nan] * len(df_temp.columns)
            df_temp = df_temp.loc[order, ]
        df_temp = df_temp.fillna(0).reset_index()
        df_temp = df_temp.sort_values(by='index', ascending=True)
        fig = go.Figure()
        annotations = []
        for row, color in zip(range(len(df_temp)), ['rgb(60,54,50)', 'rgb(222,46,37)','rgb(132,29,22)']):
            fig.add_trace(go.Bar(
                y=[''],
                x=[df_temp.loc[row, column]],
                name=df_temp.loc[row, 'index'],
                text=df_temp.loc[row, 'index'],
                orientation='h',
                marker=dict(color=color)
            ))
        # labeling the first percentage of each bar (x_axis)
        if df_temp.loc[0, column] > 5:
            annotations.append(dict(xref='x', yref='y',
                                    x=df_temp.loc[0, column] / 2, y=0,
                                    text=' ' + str(df_temp.loc[0, column]) + '%' + '<br> <span style="font-size: 25px;">' + df_temp.loc[0, 'index'] + '</span>',
                                    font=dict(family='Hevletica Neue', size=40,
                                              color='rgb(255, 255, 255)'),
                                    showarrow=False))
        space = df_temp.loc[0, column]
        for i in range(1, len(df_temp[column])):
            # labeling the rest of percentages for each bar (x_axis)
            if df_temp.loc[i, column] > 5:
                annotations.append(dict(xref='x', yref='y',
                                        x=space + (df_temp.loc[i, column] / 2), y=0,
                                        text=' ' + str(df_temp.loc[i, column]) + '%' + '<br> <span style="font-size: 25px;">' + df_temp.loc[i, 'index'] + '</span>',
                                        font=dict(family='Hevletica Neue', size=40,
                                                  color='rgb(255, 255, 255)'),
                                        showarrow=False, align="center"))
            space += df_temp.loc[i, column]
        fig.update_layout(
            xaxis=dict(
                showgrid=False,
                showline=False,
                showticklabels=False,
                zeroline=False
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                showticklabels=False,
                zeroline=False,
            ),
            barmode='stack',
            plot_bgcolor='rgb(255, 255, 255)',
            showlegend=True,
            annotations = annotations
        )
        fig.update_layout(font_family='Hevletica Neue',
                          legend=dict(
                              orientation="h",
                              yanchor="bottom",
                              y=-0.02,
                              xanchor="center",
                              x=0.48,
                              font = dict(size = 20, color = "black")
                          ))
        fig.show()

    def bar_with_errors(self):

        fig = go.Figure()
        x = list(self.df['Course']).copy()
        x = self.capitalize_list(x)
        for ind, val in enumerate(x):
            if len(val) >= 18:
                x[ind] = x[ind].replace(val, re.sub('(' + '\s\S*?' * 2 + ')\s',
                                                    r'\1<br> ',
                                                    val))
        fig.add_trace(go.Bar(
            name='Control',
            x=x, y=[round(i, 1) for i in self.df['Average Score']],
            error_y=dict(type='data', color=self.color_palette[-3], array=np.array(self.df['Average Score']) * 0.1),
            marker_color=self.color_palette[-1],
            texttemplate='%{y}', textposition='inside',
            insidetextanchor = 'middle'
        ))
        fig.update_layout(
            font_family='Hevletica Neue',
            title='Average Outcome by Course',
            xaxis_tickfont_size=14,
            xaxis=dict(
                title='',
                titlefont_size=16,
                tickfont_size=12,
            ),
            yaxis=dict(
                title='Average Outcome',
                titlefont_size=16,
                tickfont_size=12
            ),
            bargap=0.25, # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        #fig.write_image("fig.png", height=550, width=900, scale=10)
        fig.show()

    def stacked_bar_plot(self, course_var, first_var, second_var, y_title, perc, title, include_total):
        fig = go.Figure()
        if include_total:
            df = self.df
        else:
            df = self.df.iloc[:-1, :]
        x = list(df[course_var]).copy()
        x = self.capitalize_list(x)
        for ind, val in enumerate(x):
            if len(val) >= 18:
                x[ind] = x[ind].replace(val, re.sub('(' + '\s\S*?' * 2 + ')\s',
                                                    r'\1<br> ',
                                                    val))
        fv = df[first_var] * 100 if perc else df[first_var]
        sv = df[second_var] * 100 if perc else df[second_var]
        fig.add_trace(go.Bar(
            name=first_var,
            x=x, y=[round(i, 1) for i in fv],
            marker_color=self.color_palette[-2],
            texttemplate='%{y}', textposition='outside', textfont_size=16
        ))
        fig.add_trace(go.Bar(
            name=second_var,
            x=x, y=[round(i, 1) for i in sv],
            marker_color='rgb(232,148,60)',
            texttemplate='%{y}', textposition='outside', textfont_size=16
        ))
        fig.update_layout(
            font_family='Hevletica Neue',
            title=title if title else '',
            xaxis_tickfont_size=16,
            xaxis=dict(
                title='',
                titlefont_size=16,
                tickfont_size=16,
            ),
            yaxis=dict(
                title=y_title,
                titlefont_size=16,
                tickfont_size=16
            ),
            bargap=0.25, # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            legend = dict(font = dict(family = "Hevletica Neue", size = 16)))
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.update_layout(barmode='stack')
        #fig.write_image("fig.png", height=550, width=900, scale=10)
        fig.show()

    def create_simple_bar(self, course_col, col, perc, y_title, title, avg_line_title, inside_outside_pos):
        df = self.df.iloc[:-1, :]
        overall = self.df.loc[len(self.df) - 1, col]
        x = list(df[course_col]).copy()
        x = self.capitalize_list(x)
        for ind, val in enumerate(x):
            if len(val) >= 18:
                x[ind] = x[ind].replace(val, re.sub('(' + '\s\S*?' * 1 + ')\s',
                                                    r'\1<br> ', val))
        v = self.df[col] * 100 if perc else self.df[col]
        fig = go.Figure([go.Bar(x=x, y=[round(i, 1) for i in v],
                                marker_color=self.color_palette[-3],
                                texttemplate='%{y}', textposition=inside_outside_pos,
                                showlegend=False, textfont_size=16),
                         go.Scatter(x=x, y=[round(overall, 1)] * len(x),
                                    marker_color=self.color_palette[-1],
                                    name=avg_line_title)])
        fig.add_annotation(x=x[-2], y=overall + overall * 0.05,
                           text='Average = ' + str(overall),
                           showarrow=False,
                           yshift=10)
        fig.update_layout(
            font_family='Hevletica Neue',
            font_size = 16,
            title = title if title else '',
            xaxis_tickfont_size=16,
            xaxis=dict(
                title='',
                titlefont_size=16,
                tickfont_size=16,
            ),
            yaxis=dict(
                title=y_title,
                titlefont_size=16,
                tickfont_size=16
            ),
            bargap=0.25, # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            legend = dict(font = dict(family = "Hevletica Neue", size = 16)
                          ))
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        #fig.write_image("fig.png", height=550, width=900, scale=10)
        fig.show()

    def plot_line(self, time_col, list_of_cols, title, y_title, x_title):
        fig = go.Figure()
        for ind, col in enumerate(list_of_cols):
            fig.add_trace(go.Scatter(y=self.df[col], x=self.df[time_col],
                                     mode='lines+text',
                                     name=col,
                                     line=dict(color=self.color_palette2[ind + 1], width=4)))
        fig.update_layout(
            font_family='Arial',
            font_size = 16,
            title = title if title else '',
            xaxis_tickfont_size=16,
            xaxis=dict(
                title=x_title,
                titlefont_size=16,
                tickfont_size=16,
                tickformat='%b, %d'
            ),
            yaxis=dict(
                title=y_title,
                titlefont_size=16,
                tickfont_size=16
            ),
            template=self.large_rockwell_template,
            legend = dict(font = dict(family = "Arial", size = 16)),
            #margin=dict(l=0, r=0, b=10, pad=100)
        )
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(showgrid=False, tickangle=0, automargin=True)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                          plot_bgcolor='rgba(0,0,0,0)')
        fig.write_image("fig.png", height=550, width=900, scale=10)
        fig.show()



