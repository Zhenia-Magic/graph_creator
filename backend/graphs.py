import pandas as pd
import plotly.graph_objects as go
from typing import Optional, List
import re
import numpy as np
from copy import deepcopy
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import summary_table
from math import isclose, sqrt

pd.options.mode.chained_assignment = None

order = []


class DataAnalyzer:
    large_rockwell_template = dict(
        layout=go.Layout(title_font=dict(family="Hevletica", size=24))
    )
    color_2 = ["#ef4137", "#322864"]
    color_4 = ["#853565", "#f0a81b", "#5b3e97", "#ef4137"]
    color_5 = ["#a03068", "#da1c4f", "#ef4137", "#f47622", "#f0a81b"]
    color_6 = ["#f0a81b", "#a7427e", "#da1c4f", "#85b941", "#19a6b4", "#322864"]
    color_8 = ["#7d66ad", "#322864", "#ef4137", "#da1c4f", "#e4d52e", "#85b941", "#4bbfad", "#117891"]
    color_10 = ["#a7427e", "#5b3e97", "#efb91c", "#ef4137", "#da1c4f", "#e4d52e", "#85b941", "#34ab7c",
                "#19a6b4", "#322864"]

    def __init__(self, data: pd.DataFrame):
        self.df = data

    def get_palette(self, length: int):
        if length == 1:
            return ["#ef4137"]
        elif length == 2:
            return self.color_2
        elif length in [3, 4]:
            return self.color_4[:length]
        elif length == 5:
            return self.color_5
        elif length == 6:
            return self.color_6
        elif length in [7, 8]:
            return self.color_8[:length]
        elif length in [9, 10]:
            return self.color_10[:length]

    @staticmethod
    def read_data(data: str) -> pd.DataFrame:
        df = pd.read_csv(data)
        return df

    def show_data(self) -> pd.DataFrame:
        return self.df

    @staticmethod
    def capitalize_list(list_name):
        return [i.capitalize() for i in list_name]

    @staticmethod
    def error_gen(actual: float, rounded: float):
        divisor = sqrt(1.0 if actual < 1.0 else actual)
        return abs(rounded - actual) ** 2 / divisor

    def round_to_100(self, percents: np.ndarray):
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

    def create_bar_graph(self, column: str, title: Optional[bool] = False, title_text: Optional[str] = None,
                         order: Optional[str] = None,
                         x_title: Optional[str] = None, y_title: Optional[str] = None,
                         one_color: bool = True, width: int = 900, height: int = 550,
                         font_size: int = 20, font: str = 'Hevletica Neue', max_symb: int = 20,
                         transparent: bool = False, percents: bool = True,
                         bar_gap: Optional[float] = None, y_range: Optional[list] = None,
                         tick_distance: Optional[float] = None):
        if percents:
            df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(normalize=True))
            df_temp[column] = np.array(self.round_to_100(np.array(df_temp[column] * 100))) / 100
        else:
            df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts())
        new_order = order.split(',\n')
        if new_order:
            not_in_df = [index for index in new_order if index not in set(list(
                df_temp.index))]
            for i in not_in_df:
                df_temp.loc[i, :] = [np.nan] * len(df_temp.columns)
            df_temp = df_temp.loc[new_order,]
        df_temp = df_temp.fillna(0).reset_index()
        x = list(df_temp['index'])
        x = [split_string(string, max_symb) for string in x]
        fig = self.plot_bar(x, list(df_temp[column]), width, height, font_size, font,
                            title=title_text if title else None,
                            x_title=x_title, y_title=y_title, one_color=one_color,
                            transparent=transparent, percents=percents)
        if bar_gap is not None:
            fig.update_layout(bargap=bar_gap)
        if y_range is not None:
            fig.update_yaxes(range=y_range)
        if tick_distance is not None:
            fig.update_yaxes(dtick=tick_distance)
        return fig

    def create_bar_graph_group(self, columns: List[str], title: Optional[bool] = False,
                               title_text: Optional[str] = None, order: str = None,
                               x_title: Optional[str] = None, y_title: Optional[str] = None, max_symb: int = 20,
                               names: Optional[List[str]] = None,
                               width: int = 900, height: int = 550,
                               font_size: int = 20, font: str = 'Hevletica Neue',
                               legend_position: List[str] = ('top', 'left'),
                               transparent: bool = False, remove: bool = False, percents: bool = False,
                               multilevel_columns: bool = False, course_col: Optional[str] = None,
                               bar_gap: Optional[float] = None, bar_group_gap: Optional[float] = None,
                               y_range: Optional[list] = None,
                               tick_distance: Optional[float] = None,
                               reverse_legend_order: bool = False):
        new_order = order.split(',\n')
        palette = self.get_palette(len(new_order))
        if not multilevel_columns:
            list_vals = [self.df.loc[0, column] for column in columns]
            for ind, val in enumerate(list_vals):
                if remove:
                    title_text, list_vals[ind] = re.split(' - ', list_vals[ind])
                list_vals[ind] = split_string(list_vals[ind], max_symb)
            fig = go.Figure()
            dict_nums = {}
            for index, response in enumerate(new_order):
                list_num = []
                for column in columns:
                    df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(
                        normalize=True))
                    if response not in df_temp.index:
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
            for index, response in enumerate(new_order):
                fig.add_trace(go.Bar(x=list_vals,
                                     y=dict_nums[response][1],
                                     name=names[index] if names else response,
                                     marker_color=palette[dict_nums[response][0]],
                                     texttemplate='%{y:.0%}' if percents else '%{y:}', textposition='outside',
                                     textfont_size=font_size
                                     ))
        else:
            dict_nums = {col: list(self.df[columns][col]) for col in new_order}
            fig = go.Figure()
            col = self.df[course_col].columns[0]
            x = list(self.df[course_col][col])
            x = [split_string(string, max_symb) for string in x]
            for index, response in enumerate(new_order):
                fig.add_trace(go.Bar(x=x,
                                     y=dict_nums[response],
                                     name=names[index] if names else response,
                                     marker_color=palette[index],
                                     texttemplate='%{y:.0%}' if percents else '%{y:}', textposition='outside',
                                     textfont_size=font_size
                                     ))
        if len(legend_position) == 2:
            y_legend = 1 if legend_position[1] == 'top' else 0.5 if legend_position[1] == 'middle' else -0.3
            x_legend = 1 if legend_position[0] == 'right' else 0.5 if legend_position[0] == 'center' else -0.15
            orientation = 'h' if legend_position[0] == 'center' else 'v'
            x_anchor = 'left'
            y_anchor = 'top'

        else:
            y_legend = legend_position[1]
            x_legend = legend_position[0]
            orientation = 'v' if legend_position[4] == 'vertical' else 'h'
            x_anchor = legend_position[2]
            y_anchor = legend_position[3]
        fig.update_layout(
            font_family=font,
            font_size=font_size,
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            xaxis_tickfont_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1%' if percents else '1',
                title_standoff=25
            ),
            bargap=0.15,
            template=self.large_rockwell_template,
            legend=dict(font_size=font_size,
                        font_family=font,
                        orientation=orientation,
                        y=y_legend,
                        x=x_legend,
                        xanchor=x_anchor,
                        yanchor=y_anchor),
            width=width, height=height
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)

        if bar_gap:
            fig.update_layout(bargap=bar_gap)
        if bar_group_gap:
            fig.update_layout(bargroupgap=bar_group_gap)

        if y_range is not None:
            fig.update_yaxes(range=y_range)
        if tick_distance is not None:
            fig.update_yaxes(dtick=tick_distance)
        if reverse_legend_order:
            fig.update_layout(legend_traceorder="reversed")
        return fig

    def get_categories_from_columns(self, column: str, sep: str,
                                    order: Optional[List[str]] = None) -> pd.DataFrame:
        temp_df = self.df.copy()
        temp_df.loc[1:, column] = [re.split(sep, str(i)) for i in temp_df.loc[1:, column]]
        df_res = pd.DataFrame(columns=['count'])
        responses_num = len(temp_df.loc[1:, column])
        for index_row, tag_list in enumerate(temp_df.loc[1:, column]):
            if type(tag_list) == str:
                tag_list = [tag_list]
            for index_tag, tag in enumerate(tag_list):
                if len(tag) == 1:
                    temp_df.loc[index_row + 1, column][index_tag + 1] = tag + \
                                                                        temp_df.loc[index_row + 1, column][
                                                                            index_tag + 1]
                    continue
                tag = tag.strip()
                if tag[-1] == '.':
                    tag = tag[:-1]
                if tag in list(df_res.index):
                    df_res.loc[tag, 'count'] += 1
                else:
                    df_res.loc[tag, 'count'] = 1
        if order:
            for string in order:
                if string not in df_res.index:
                    df_res.loc[string, 'count'] = 0
        df_res = df_res.reset_index()
        df_res = df_res[df_res['index'] != 'nan']
        df_res['count'] = [i / responses_num for i in df_res['count']]
        df_res['count'] = [round(i, 2) for i in df_res['count']]
        df_res['index'] = pd.Categorical(df_res['index'], order)
        return df_res.sort_values('index')

    def create_chart_for_categories(self, column: str, title: Optional[bool] = False,
                                    title_text: Optional[str] = None, order: Optional[str] = None,
                                    x_title: Optional[str] = None, y_title: Optional[str] = None,
                                    one_color: bool = False, sep: str = ',(\S(?:(?!,\S).)*)', max_symb: int = 20,
                                    width: int = 900, height: int = 550,
                                    font_size: int = 20, font: str = 'Hevletica Neue',
                                    transparent: bool = False):
        new_order = order.split(',\n')
        df_res = self.get_categories_from_columns(column, sep, new_order)
        df_res['index'] = [split_string(string, max_symb) for string in df_res['index']]

        return self.plot_bar(df_res['index'], df_res['count'], width, height, font_size, font,
                             title=title_text if title else None,
                             x_title=x_title, y_title=y_title, one_color=one_color,
                             transparent=transparent)

    def plot_self_assessment(self, time_col: str, title: Optional[bool] = False,
                             title_text: Optional[str] = None,
                             x_title: Optional[str] = None, y_title: Optional[str] = None,
                             width: int = 900, height: int = 550,
                             font_size: int = 20, font: str = 'Hevletica Neue', max_symb: int = 20,
                             transparent: bool = False,
                             round_nums: int = 2, legend_y_coord: float = -0.3, tick_distance: Optional[float] = None,
                             y_range: Optional[list] = None, bar_gap: Optional[float] = None):
        fig = go.Figure()
        df = self.df
        df = df.set_index(time_col)
        palette = self.get_palette(2)
        x = list(df.columns)
        x = self.capitalize_list(x)
        x = [split_string(string, max_symb) for string in x]
        round_nums = int(round_nums)
        for index, response in enumerate(['Pre-semester',
                                          'Post-semester']):
            y = [round(i, round_nums) for i in df.loc[response, :]]
            fig.add_trace(go.Bar(x=x,
                                 y=y,
                                 name=response,
                                 marker_color=palette[-index],
                                 text=y, textposition='outside',
                                 textfont_size=font_size
                                 ))
        if y_range is not None:
            fig.update_yaxes(range=y_range)
        if tick_distance is not None:
            fig.update_yaxes(dtick=tick_distance)
        fig.update_layout(
            font_family=font,
            font_size=font_size,
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            xaxis_tickfont_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat="1",
                title_standoff=25
            ),
            bargap=0.6,
            template=self.large_rockwell_template,
            legend=dict(font_size=font_size,
                        font_family=font,
                        orientation='h',
                        y=float(legend_y_coord),
                        x=0.5,
                        xanchor='center',
                        yanchor='top'),
            width=width, height=height
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')
        if bar_gap is not None:
            fig.update_layout(bargap=bar_gap)
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def plot_bar(self, x: list, y: list, width: int, height: int, font_size: int,
                 font: str, title: Optional[str] = None,
                 x_title: Optional[str] = None,
                 y_title: Optional[str] = None,
                 one_color: bool = False,
                 transparent: bool = False,
                 percents: bool = True,
                 textposition: str = 'outside',
                 showlegend: bool = False,
                 error_y: Optional[list] = None,
                 insidetextanchor: str = 'end'):
        fig = go.Figure()
        error_y = dict(type='data', array=error_y)
        if one_color:
            fig.add_trace(go.Bar(x=x,
                                 y=y,
                                 marker_color='rgb(224,44,36)',
                                 error_y=error_y,
                                 texttemplate='%{y:.0%}' if percents else '%{y:}',
                                 textfont_size=font_size, textposition=textposition,
                                 insidetextanchor=insidetextanchor
                                 ))
        else:
            fig.add_trace(go.Bar(x=x,
                                 y=y,
                                 marker_color=self.get_palette(len(x)),
                                 error_y=error_y, insidetextanchor=insidetextanchor,
                                 texttemplate='%{y:.0%}' if percents else '%{y:}', textposition=textposition,
                                 ))

        fig.update_layout(

            title=title,
            title_font_family=font,
            title_font_size=font_size * 1.5,
            font_family=font,
            font_size=font_size,
            xaxis=dict(
                type='category',
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,

            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1%' if percents else '1',
                title_standoff=25
            ),
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            width=width,
            height=height,
            showlegend=showlegend
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def create_pie_chart(self, width: int, height: int, font_size: int,
                         font: str, title: Optional[str] = None, title_text: Optional[str] = None,
                         x_title: Optional[str] = None,
                         y_title: Optional[str] = None,
                         what_show: Optional[str] = None, legend_position: List[str] = ('top', 'left'),
                         transparent: bool = False, column: Optional[str] = None,
                         label_column: Optional[str] = None, numbers_column: Optional[str] = None,
                         order: Optional[str] = None
                         ):
        new_order = order.split(',\n')
        new_order = {key: i for i, key in enumerate(new_order)}
        if column:
            dictionary = dict(self.df.loc[1:, column].dropna().value_counts(normalize=True))
            labels = list(dictionary.keys())
            vals = np.array(self.round_to_100(np.array(list(dictionary.values())) * 100)) / 100
        else:
            labels = list(self.df[label_column])
            nums = np.array(list(self.df[numbers_column])) / sum(np.array(list(self.df[numbers_column])))
            vals = np.array(self.round_to_100(np.array(nums) * 100)) / 100
        labels, vals = zip(*sorted(zip(labels, vals), key=lambda d: new_order[d[0]]))
        text_temp = '%{percent:1.0%}' if what_show == 'Percent' else 'label+percent'
        palette = self.get_palette(len(labels))
        if what_show == 'Percent':
            fig = go.Figure(data=[go.Pie(labels=labels, values=vals,
                                         marker_colors=palette[:len(labels)],
                                         texttemplate=text_temp, sort=False)])
        else:
            fig = go.Figure(data=[go.Pie(labels=labels, values=vals,
                                         marker_colors=palette[:len(labels)],
                                         textinfo=text_temp, sort=False)])
        if len(legend_position) == 2:
            y_legend = 1 if legend_position[1] == 'top' else 0.5 if legend_position[1] == 'middle' else -0.3
            x_legend = 1 if legend_position[0] == 'right' else 0.5 if legend_position[0] == 'center' else -0.15
            orientation = 'h' if legend_position[0] == 'center' else 'v'
            x_anchor = 'left'
            y_anchor = 'top'
        else:
            y_legend = legend_position[1]
            x_legend = legend_position[0]
            orientation = 'v' if legend_position[4] == 'vertical' else 'h'
            x_anchor = legend_position[2]
            y_anchor = legend_position[3]
        fig.update_layout(
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            font_family=font,
            font_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1%',
                title_standoff=25
            ),
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            width=width,
            height=height,
            legend=dict(font_size=font_size,
                        font_family=font,
                        orientation=orientation,
                        y=y_legend,
                        x=x_legend,
                        xanchor=x_anchor,
                        yanchor=y_anchor),
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')
        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def create_gauge_graph(self, column: str, width: int, height: int,
                           font_size: int, font: str, transparent: bool):
        promoters = (self.df.loc[1:, column] == 'Promoter').sum() / (len(self.df) - 1)
        detractors = (self.df.loc[1:, column] == 'Detractor').sum() / (len(self.df) - 1)
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=round(100 * (promoters - detractors), 1),
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={'axis': {'range': [-100, 100]},
                   'bar': {'color': 'rgb(224,44,36)', 'thickness': 1}}))

        fig.update_layout(font_family=font, font_size=font_size, width=width,
                          height=height)
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        return fig

    def create_horizontal_bar_graph(self, column: str, order: Optional[str] = None,
                                    width: int = 900, height: int = 500,
                                    transparent: bool = False,
                                    font_size: int = 20, font: str = 'Hevletica Neue'):
        new_order = order.split(',\n')
        df_temp = pd.DataFrame(self.df.loc[1:, column].value_counts(
            normalize=True))
        df_temp[column] = self.round_to_100(np.array(df_temp[column] * 100))
        if new_order:
            not_in_df = [index for index in new_order if index not in set(list(
                df_temp.index))]
            for i in not_in_df:
                df_temp.loc[i, :] = [np.nan] * len(df_temp.columns)
            df_temp = df_temp.loc[new_order, ]
        df_temp = df_temp.fillna(0).reset_index()
        df_temp = df_temp.sort_values(by='index', ascending=True)
        fig = go.Figure()
        annotations = []
        for row, color in zip(range(len(df_temp)), ['rgb(60,54,50)', 'rgb(222,46,37)', 'rgb(132,29,22)']):
            fig.add_trace(go.Bar(
                y=[''],
                x=[df_temp.loc[row, column]],
                name=df_temp.loc[row, 'index'],
                orientation='h',
                marker=dict(color=color)
            ))
        # labeling the first percentage of each bar (x_axis)
        if df_temp.loc[0, column] > 5:
            annotations.append(dict(xref='x', yref='y',
                                    x=df_temp.loc[0, column] / 2, y=0,
                                    text=' ' + str(
                                        int(df_temp.loc[0, column])) + '%' + '<br> <span style="font-size: 25px;">' +
                                            df_temp.loc[0, 'index'] + '</span>',
                                    font=dict(family=font, size=font_size,
                                              color='rgb(255, 255, 255)'),
                                    showarrow=False))
        space = df_temp.loc[0, column]
        for i in range(1, len(df_temp[column])):
            # labeling the rest of percentages for each bar (x_axis)
            if df_temp.loc[i, column] > 5:
                annotations.append(dict(xref='x', yref='y',
                                        x=space + (df_temp.loc[i, column] / 2), y=0,
                                        text=' ' + str(
                                            int(df_temp.loc[
                                                    i, column])) + '%' + '<br> <span style="font-size: 25px;">' +
                                             df_temp.loc[i, 'index'] + '</span>',
                                        font=dict(family=font, size=font_size,
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
            annotations=annotations,
            width=width,
            height=height
        )
        fig.update_layout(font_family=font,
                          legend=dict(
                              orientation="h",
                              yanchor="bottom",
                              y=-0.05,
                              xanchor="center",
                              x=0.48,
                              font=dict(size=font_size / 2, color="black"),
                              traceorder='normal'
                          ))
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        return fig

    def create_simple_bar(self, avg_line_title: str, average_line_x: str,
                          course_col: str, column: str, y_range: Optional[list] = None,
                          title: Optional[bool] = False, title_text: Optional[str] = None,
                          order: Optional[str] = None,
                          x_title: Optional[str] = None, y_title: Optional[str] = None,
                          one_color: bool = True, width: int = 900, height: int = 550,
                          font_size: int = 20, font: str = 'Hevletica Neue', max_symb: int = 20,
                          transparent: bool = False, percents: bool = True,
                          inside_outside_pos: str = 'outside', show_average: bool = False,
                          round_nums: int = 2, err_column: Optional[str] = None,
                          tick_distance: Optional[float] = None,
                          bar_gap: Optional[float] = None
                          ):
        df = deepcopy(self.df)
        overall = sum(self.df.loc[:, column]) / len(self.df.loc[:, column])
        new_order = order.split(',\n')
        df = df.set_index(course_col)
        if new_order:
            not_in_df = [index for index in new_order if index not in set(list(
                df.index))]
            for i in not_in_df:
                df.loc[i, :] = [np.nan] * len(df.columns)
            df = df.loc[new_order, ]
        df = df.fillna(0).reset_index()
        x = list(df[course_col]).copy()
        x_copy = x.copy()
        x = [split_string(string, max_symb) for string in x]
        v = df[column]
        if err_column is not None:
            insidetextanchor = 'middle'
            inside_outside_pos = 'inside'
        else:
            insidetextanchor = 'end'
        fig = self.plot_bar(x, [round(i, int(round_nums)) for i in v], width, height, font_size, font,
                            title=title_text if title else None,
                            x_title=x_title, y_title=y_title, one_color=one_color,
                            error_y=df[err_column] if err_column else None,
                            transparent=transparent, percents=percents, textposition=inside_outside_pos,
                            showlegend=False, insidetextanchor=insidetextanchor)
        if y_range is not None:
            fig.update_yaxes(range=y_range)
        if tick_distance is not None:
            fig.update_yaxes(dtick=tick_distance)

        if bar_gap is not None:
            fig.update_layout(bargap=bar_gap)

        if show_average:
            fig.add_trace(go.Scatter(x=x, y=[round(overall, int(round_nums))] * len(x),
                                     marker_color=self.get_palette(len(x))[-1],
                                     name=avg_line_title))
            addition = '%' if percents else ''
            num = round(overall, int(round_nums)) * 100 if percents else round(overall, int(round_nums))
            num = round(num, int(round_nums))
            if num % 1 == 0:
                num = int(num)
            num = str(num)
            ind = x_copy.index(average_line_x)
            fig.add_annotation(x=x[ind], y=overall + overall * 0.05,
                               text='Average = ' + num + addition,
                               showarrow=False,
                               yshift=10)
        return fig

    def plot_line(self, time_col, title: Optional[bool] = False,
                  title_text: Optional[str] = None, y_range: Optional[list] = None,
                  x_title: Optional[str] = None, y_title: Optional[str] = None,
                  width: int = 900, height: int = 550,
                  font_size: int = 20, font: str = 'Hevletica Neue',
                  transparent: bool = False, tick_distance: Optional[float] = None,
                  show_average: bool = False):

        fig = go.Figure()
        cols = list(self.df.columns)
        cols.remove(time_col)

        if show_average:
            colors = self.get_palette(len(cols) + 1)
        else:
            colors = self.get_palette(len(cols))

        index = 0
        for ind, col in enumerate(cols):
            df_new = self.df.dropna(subset=col)
            fig.add_trace(go.Scatter(y=df_new[col], x=pd.to_datetime(df_new[time_col]),
                                     mode='lines+text',
                                     name=col,
                                     line=dict(color=colors[ind], width=4)))
            index += 1
        if show_average:
            means = []
            dates = self.df[time_col]
            df_indexed = self.df.set_index(time_col)
            for date in dates:
                means.append(df_indexed.loc[date, :].mean())
            fig.add_trace(go.Scatter(y=means, x=pd.to_datetime(self.df[time_col]),
                                     mode='lines+text',
                                     name='Average',
                                     line=dict(color=colors[index], width=4, dash='dash')))
        fig.update_layout(
            font_family=font,
            font_size=font_size,
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            xaxis_tickfont_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='%b, %d'
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat="1",
                title_standoff=width * 0.02
            ),
            template=self.large_rockwell_template,
            legend=dict(font_size=font_size,
                        font_family=font),
            width=width, height=height
        )
        if y_range is not None:
            fig.update_yaxes(range=y_range)
        if tick_distance is not None:
            fig.update_yaxes(dtick=tick_distance)

        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def plot_horizontal_bar_for_nps(self,
                                    course_col: str, column: str, title: Optional[bool] = False,
                                    title_text: Optional[str] = None,
                                    x_title: Optional[str] = None, y_title: Optional[str] = None,
                                    width: int = 900, height: int = 550,
                                    font_size: int = 20, font: str = 'Hevletica Neue', max_symb: int = 20,
                                    transparent: bool = False, percents: bool = True,
                                    round_nums: int = 2):
        df = deepcopy(self.df)
        df = df.set_index(course_col)
        df = df.fillna(0).reset_index()
        x = list(df[course_col]).copy()
        x = [split_string(string, max_symb) for string in x]
        v = self.df[column]
        fig = go.Figure()
        fig.add_trace(go.Bar(y=x, x=[round(i, int(round_nums)) for i in v],
                             marker_color='rgb(224,44,36)',
                             texttemplate='%{x}' if percents else '%{x}%',
                             textfont_size=font_size, orientation='h',
                             textposition='outside'
                             ))
        fig.update_xaxes(range=[-120, 120])
        fig.update_layout(
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            font_family=font,
            font_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1%' if percents else '1',
                title_standoff=25
            ),
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            width=width,
            height=height,
            barmode='relative'
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=False, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def stacked_bar_plot(self, column: str, first_column: str, second_column: str,
                         title: Optional[bool] = False, title_text: Optional[str] = None,
                         x_title: Optional[str] = None, y_title: Optional[str] = None,
                         width: int = 900, height: int = 550,
                         font_size: int = 20, font: str = 'Hevletica Neue',
                         transparent: bool = False, percents: bool = True,
                         max_symb: int = 20, legend_position: List[str] = ('bottom', 'center')):
        fig = go.Figure()
        df = self.df
        x = list(df[column]).copy()
        x = self.capitalize_list(x)
        x = [split_string(string, max_symb) for string in x]
        fig.add_trace(go.Bar(
            name=first_column,
            x=x, y=[round(i, 2) for i in df[first_column]],
            marker_color=self.get_palette(2)[-1],
            texttemplate='%{y}', textposition='outside', textfont_size=font_size
        ))
        fig.add_trace(go.Bar(
            name=second_column,
            x=x, y=[round(i, 2) for i in df[second_column]],
            marker_color=self.get_palette(2)[0],
            texttemplate='%{y}', textposition='outside', textfont_size=font_size
        ))
        if len(legend_position) == 2:
            y_legend = 1 if legend_position[1] == 'top' else 0.5 if legend_position[1] == 'middle' else -0.3
            x_legend = 1 if legend_position[0] == 'right' else 0.5 if legend_position[0] == 'center' else -0.15
            orientation = 'h' if legend_position[0] == 'center' else 'v'
            x_anchor = 'left'
            y_anchor = 'top'
        else:
            y_legend = legend_position[1]
            x_legend = legend_position[0]
            orientation = 'v' if legend_position[4] == 'vertical' else 'h'
            x_anchor = legend_position[2]
            y_anchor = legend_position[3]

        fig.update_layout(

            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            font_family=font,
            font_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1%' if percents else '1',
                title_standoff=25
            ),
            bargap=0.15,  # gap between bars of adjacent location coordinates.
            template=self.large_rockwell_template,
            width=width,
            height=height,
            showlegend=True,
            legend=dict(font_size=font_size,
                        font_family=font,
                        orientation=orientation,
                        y=y_legend,
                        x=x_legend,
                        xanchor=x_anchor,
                        yanchor=y_anchor),
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        fig.update_layout(barmode='stack')
        return fig

    def plot_histogram(self, column: str,
                       title: Optional[bool] = False, title_text: Optional[str] = None,
                       x_title: Optional[str] = None, y_title: Optional[str] = None,
                       width: int = 900, height: int = 550,
                       font_size: int = 20, font: str = 'Hevletica Neue',
                       transparent: bool = False):
        fig = go.Figure(data=[go.Histogram(x=self.df[column], marker_color='rgb(222,46,37)')])
        fig.update_layout(
            title=title_text if title else '',
            title_font_family=font,
            title_font_size=font_size * 1.5,
            font_family=font,
            font_size=font_size,
            xaxis=dict(
                title=x_title if x_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size
            ),
            yaxis=dict(
                title=y_title if y_title else '',
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1',
                title_standoff=25
            ),
            template=self.large_rockwell_template,
            width=width,
            height=height
        )
        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')

        fig.update_xaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showline=True, linewidth=1, linecolor='black')
        fig.update_yaxes(showgrid=False, gridwidth=1, gridcolor='lightgrey', automargin=True)
        fig.update_xaxes(tickangle=0, automargin=True)
        return fig

    def plot_scatter_with_regression(self, first_column: str, second_column: str,
                                     title: Optional[bool] = False, title_text: Optional[str] = None,
                                     x_title: Optional[str] = None, y_title: Optional[str] = None,
                                     width: int = 900, height: int = 550,
                                     font_size: int = 20, font: str = 'Hevletica Neue',
                                     transparent: bool = False, marker_size: int = 10, marker_line_width: int = 2):
        df = self.df
        y = np.array([float(i) for i in df[first_column]])
        x = np.array([float(i) for i in df[second_column]])
        x_regr = sm.add_constant(x)
        res = sm.OLS(y, x_regr).fit()

        st, data, ss2 = summary_table(res, alpha=0.05)
        preds = pd.DataFrame.from_records(data, columns=[s.replace('\n', ' ') for s in ss2])
        preds['displ'] = x
        preds = preds.sort_values(by='displ')

        fig = go.Figure()
        p1 = go.Scatter(**{
            'mode': 'markers', 'marker_line_width': marker_line_width, 'marker_size': marker_size,
            'marker_color': 'rgb(222,46,37)',
            'x': x,
            'y': y,
            'name': 'Points'
        })
        p2 = go.Scatter({
            'mode': 'lines',
            'x': preds['displ'],
            'y': preds['Predicted Value'],
            'name': 'Regression',
            'line': {
                'color': 'rgb(215,116,102)'
            }
        })
        # Add a lower bound for the confidence interval, white
        p3 = go.Scatter({
            'mode': 'lines',
            'x': preds['displ'],
            'y': preds['Mean ci 95% low'],
            'name': 'Lower 95% CI',
            'showlegend': False,
            'line': {
                'color': 'white'
            }
        })
        # Upper bound for the confidence band, transparent but with fill
        p4 = go.Scatter({
            'type': 'scatter',
            'mode': 'lines',
            'x': preds['displ'],
            'y': preds['Mean ci 95% upp'],
            'name': '95% CI',
            'fill': 'tonexty',
            'line': {
                'color': 'white'
            },
            'fillcolor': 'rgba(215,116,102, 0.3)'
        })
        fig.add_trace(p1)
        fig.add_trace(p2)
        fig.add_trace(p3)
        fig.add_trace(p4)
        fig.update_layout(
            font_family=font,
            title=title_text if title else '',
            title_font_family=font,
            xaxis=dict(
                title=x_title,
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1',
            ),
            yaxis=dict(
                title=y_title,
                titlefont_size=font_size,
                tickfont_size=font_size,
                tickformat='1',
                title_standoff=width * 0.01
            ),
            template=dict(
                layout=go.Layout(title_font=dict(family=font, size=font_size * 1.5))
            ),
            width=width,
            height=height,
            legend=dict(font=dict(family=font, size=font_size)),
            margin=dict(
                l=150,
                r=50,
                b=100,
                t=100,
                pad=4
            ),
        )

        if transparent:
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',
                              plot_bgcolor='rgba(0,0,0,0)')
        else:
            fig.update_layout(plot_bgcolor='rgb(255,255,255)')
        return fig


def split_string(string, max_symb):
    new_str_list = string.split(" ")
    whole_str = ""
    new_str = ""
    end = False
    ind = 0
    if len(new_str_list) == 1 and len(new_str_list[0]) > max_symb:
        return string
    if max([len(w) for w in new_str_list]) > max_symb:
        raise ValueError('number of symbols is too low. Increase it.')
    while not end:
        if len(new_str) + len(new_str_list[ind]) <= max_symb:
            if new_str == "":
                new_str += new_str_list[ind]
            else:
                new_str = new_str + " " + new_str_list[ind]
            ind += 1
            if ind == len(new_str_list):
                whole_str += new_str + '<br>'
                end = True
        else:
            whole_str += new_str + '<br>'
            new_str = ""
    return whole_str
