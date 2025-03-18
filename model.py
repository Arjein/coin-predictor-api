from transformers import AutoProcessor
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import math
import os
import tempfile
import torch
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from transformers import EarlyStoppingCallback, Trainer, TrainingArguments, set_seed
from transformers.integrations import INTEGRATION_TO_CALLBACK
from tsfm_public import (
    TimeSeriesForecastingPipeline,
    TimeSeriesPreprocessor,
    TinyTimeMixerForPrediction,
    TrackingCallback,
    count_parameters,
    get_datasets,
    TrackingCallback,
    count_parameters,
    get_datasets,
    
)
from tsfm_public.toolkit.get_model import get_model
from tsfm_public.toolkit.time_series_preprocessor import prepare_data_splits
from time import time

from data_preprocess import preprocess_data

set_seed(42)

class BNBPredictor():
    def __init__(self, path_to_model, device= 'cpu'):
        self.path_to_model = path_to_model
        self.device = device
        self.batch_size = 64
        self.context_length = 512
        self.prediction_length = 48
        # self.timestamp_column = 'open_time'
        # self.id_columns = ['symbol']
        self.target_columns = ['high', 'low','close']
        # self.control_columns = [
        #     "volume",
        #     "EMA_12",
        #     "RSI_12",
        #     "ATR_14",
        #     "Pivot_R2", "Pivot_S2",
        #     "dow_sin", "dow_cos", "hour_sin", "hour_cos", "month_sin", "month_cos", "isweekend",
        #     "log_return",
        #     "open",
        # ]
        # self.column_specifiers = {
        #     "timestamp_column": self.timestamp_column,
        #     "id_columns": self.id_columns,
        #     "target_columns": self.target_columns,
        #     "control_columns": self.control_columns,
        # }

        self.tsp = TimeSeriesPreprocessor.from_pretrained(self.path_to_model)
        
        self.model = get_model(
            self.path_to_model,
            context_length=self.context_length,
            prediction_length=self.prediction_length,
            #num_input_channels=self.tsp.num_input_channels,
            # decoder_mode="mix_channel",
            # prediction_channel_indices=self.tsp.prediction_channel_indices,
            # exogenous_channel_indices=self.tsp.exogenous_channel_indices,
            # fcm_context_length=12,
            # fcm_use_mixer=True,
            # fcm_mix_layers=2,
            # enable_forecast_channel_mixing=True,
            # fcm_prepend_past=True,
            # loss='mae',
        )
        
        self.prediction_pipeline = TimeSeriesForecastingPipeline(
            self.model,
            device=self.device,  
            feature_extractor=self.tsp,
            explode_forecasts=True
        )


    def predict(self, X_forecast, preprocess: bool = False):
        #print('Before Preprocessing:', X_forecast)
        if preprocess:
            X = preprocess_data(X_forecast)
        else:
            X = X_forecast
        #print('After Preprocessing:', X)
        df = self.prediction_pipeline(X)
        #print('Predictions Dataframe:', df)
        high_preds = df.groupby('open_time')['high'].mean().reset_index()
        low_preds = df.groupby('open_time')['low'].mean().reset_index()
        close_preds = df.groupby('open_time')['close'].mean().reset_index()
        merged_preds = high_preds.merge(low_preds, on='open_time').merge(close_preds, on='open_time')
        
        df['open'] = df['close'].shift(1)
    
        df['open_time'] = df['open_time'].astype('int64') // 10**6
        order = ['open_time','open','high','low','close']
        # Drop missing rows
        df = df.dropna()
        
        self.last_predictions = df[order]
        #print('Returning:', df)
        return df[order]
    




