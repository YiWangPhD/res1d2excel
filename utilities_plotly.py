#!/usr/bin/env python
# coding: utf-8

# Author: Yi Wang
# this is utilities for plotly and pandas


import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def draw_graph(dfList, yaxisTitle = '', xaxisRange = [], width = None, height = None, to_html = False, to_image = False):
    fig = go.Figure()
    
    for df in dfList:
        for column in df:
            # Add traces for results
            fig.add_trace(go.Scatter(x=df.index, y=df[column], mode='lines', name=column))
    if width is not None:
        fig.update_layout(width=width)
    if height is not None:
        fig.update_layout(height=height)
    if len(xaxisRange) > 0:
        fig.update_xaxes(range = xaxisRange)
    if len(yaxisTitle) > 0:
        fig.update_layout(yaxis_title = yaxisTitle)        
    fig.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    if to_html:
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    elif to_image:
        return fig
    else:
        fig.show()


def draw_sub_graphs(dfLists, title = '', width = None, height = None, ylim = True, to_html = False):
    subplots = len(dfLists)
    maxs = []
    mins = []
    
    fig = make_subplots(rows = 1, cols = subplots, horizontal_spacing = 0.03)
    
    for icol, dfList in enumerate(dfLists):
        icolor = 0
        for df in dfList:
            maxs.extend(list(df.max(axis = 0)))
            mins.extend(list(df.min(axis = 0)))
            for column in df:
                # Add traces for results
                fig.add_trace(go.Scatter(x = df.index, y = df[column], mode = 'lines', name = column, 
                                         line=dict(color=['red', 'blue', 'green','orange', 'brown', 'purple', 'yellow', 'cyan', 'magenta', 'grey'][icolor])), 
                              row = 1, col = icol + 1)
                icolor = (icolor + 1)
    if width is not None:
        fig.update_layout(width=width)
    if height is not None:
        fig.update_layout(height=height)        
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20))
    fig.update_layout(showlegend=False,  title=title,)
    if isinstance(ylim, tuple) or isinstance(ylim, list):
        if len(ylim) == 2:
            fig.update_yaxes(range=list(ylim))
        else:
            pass
    elif ylim:
        if(len(maxs) > 0 and len(mins) > 0):
            maxofmaxs = np.nanmax(maxs)
            minofmins = np.nanmin(mins)
            if maxofmaxs == minofmins:
                if maxofmaxs == 0:
                    fig.update_yaxes(range=[-1, 1])
                else:
                    fig.update_yaxes(range=[maxofmaxs - 0.5 * abs(maxofmaxs), maxofmaxs + 0.5 * abs(maxofmaxs)])
            else:
                fig.update_yaxes(range=[minofmins - 0.1 * (maxofmaxs - minofmins), maxofmaxs + 0.1 * (maxofmaxs - minofmins)])
    else:
        pass
    if to_html:
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        fig.show()


def draw_table(headerValues, cellValues, height = None, to_html = False):
    aligns=['right']+['center']*(len(cellValues) - 1)
    fig = go.Figure(data=[go.Table(
        header=dict(values=headerValues, align = 'center'), 
        cells=dict(values=cellValues, align = aligns)
    )])
    if height is not None:
        fig.update_layout(height=height)
    if to_html:
        return fig.to_html(full_html=False, include_plotlyjs='cdn')
    else:
        fig.show()


def main():
    print("in utilities_plotly.py!")


if __name__ == '__main__' and '__file__' not in globals():
    main()

