"""
Original Code from
Asynchronitätstolerante Datenintegration für IIoT-Sensoren durch Industrie 4.0 Asset Administration Shells (AAS),

author=Hilbert, Frank and Soler Perez Olaya, Santiago and Wollschlaeger, Martin

changed for sensor model
"""
from typing import Dict

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from statsmodels.tsa.arima.model import ARIMA

from src.domain.model.sensor import Sensor
from src.domain.model.synchronization_mode import SynchronizationMode


class ExtrapolationHelper:

    @staticmethod
    def synchronize_data(extrapolation_timespan:timedelta, sensors: Dict[bytes, Sensor], synchronization_mode: SynchronizationMode = SynchronizationMode.SYNCHRONIZE):
        """
        changes:
            endtime is now datetime.now
            starttime is now an extrapolation timespan
            Sensor-specific interpolation tweaks removed
            mapping from own sensor model to AAS sensor model
            especially mapping specific field, dor multiple fields for a sensor
            merging to more useful representation for endpoint -> pandas dataframe not language agnostic
            replaced general sampling rate with sensor specific sampling rate
            refactored method static
            added synchronization modes
        :param synchronization_mode:
        :param extrapolation_timespan:
        :param sensors:
        :return:
        """
        end_time = datetime.now()
        start_time = end_time - extrapolation_timespan

        if synchronization_mode == SynchronizationMode.SYNCHRONIZE:
            time_vector = pd.date_range(start_time, end_time,
                                        freq=f"{1}s") # TODO could be replaced with parameter in future
            sync_df = pd.DataFrame(index=time_vector)  # sensor values
            quality_df = pd.DataFrame(index=time_vector)  # QualityQualifier
            method_df = pd.DataFrame(index=time_vector)  # MethodQualifier

        synchronized_data = {}

        for device_address in sensors.keys():
            synchronized_data[device_address] = {}
            if synchronization_mode != SynchronizationMode.SYNCHRONIZE:
                time_vector = pd.date_range(start_time, end_time,
                                            freq=f"{sensors[device_address].expected_value_interval.seconds}s")
            for field in sensors[device_address].fields.keys():

                field_data = [{"value":data[field], "timestamp":data["receive_time"]} for data in sensors[device_address].last_values]

                df = pd.DataFrame(field_data).set_index("timestamp").sort_index()
                if df.empty:
                    continue

                last_measurement = df.index[-1]

                # Default: linear interpolation
                series_interp = df['value'].reindex(df.index.union(time_vector)).interpolate("linear")
                series = series_interp.reindex(time_vector)

                # Initialize qualifiers
                quality = pd.Series("interpolated", index=time_vector)
                method = pd.Series("linear", index=time_vector)

                # Mark measured values
                measured_idx = df.index.intersection(time_vector)
                quality.loc[measured_idx] = "measured"
                method.loc[measured_idx] = "--"
                ################################################
                # unused in this version
                #
                # Sensor-specific interpolation tweaks
                #if sensor == "Humidity":
                #    series_interp = df['value'].reindex(df.index.union(time_vector)) \
                #        .interpolate(method="pchip", order=3)
                 #   series = series_interp.reindex(time_vector)
                #    interpolated_mask = quality == "interpolated"
                #    method.loc[interpolated_mask] = "pchip"

                # -------- Extrapolation (after last measurement) --------
                extrapolation_mask = time_vector > last_measurement
                if extrapolation_mask.any():
                    target_extrap_index = time_vector[extrapolation_mask]
                    native_period = sensors[device_address].expected_value_interval.seconds
                    # TODO -> future work, calculate real (p,d,q) value
                    order = (2, 0, 2)
                    # TODO -> change if needed "ma-3"
                    method_name = "arma-2-2"

                    if sensors[device_address].fields[field]["datatype"] in ("int", "float", "double"):
                        horizon_sec = (target_extrap_index[-1] - last_measurement).total_seconds()
                        steps_native = int(np.ceil(horizon_sec / native_period))
                        min_required = 10

                        if len(df['value']) >= min_required and steps_native > 0:
                            try:
                                model = ARIMA(df['value'].values, order=order, trend='c')
                                fitted = model.fit(method_kwargs={"maxiter": 200})
                                yhat_native = fitted.forecast(steps=steps_native)

                                # Native time stamps
                                native_times = [last_measurement + timedelta(seconds=native_period * k)
                                                for k in range(1, steps_native + 1)]
                                fc_native = pd.Series(yhat_native, index=pd.to_datetime(native_times))

                                # Anchor with last measured point
                                anchor = pd.Series({pd.to_datetime(last_measurement): series.loc[last_measurement]})
                                base = pd.concat([anchor, fc_native]).sort_index()

                                # Upsample to 1 Hz extrap index
                                fc_1hz = (
                                    base.reindex(base.index.union(target_extrap_index))
                                    .sort_index()
                                    .interpolate("linear")
                                    .reindex(target_extrap_index)
                                )

                                series.loc[target_extrap_index] = fc_1hz.values
                                quality.loc[target_extrap_index] = "extrapolated"
                                method.loc[target_extrap_index] = method_name
                            except Exception as e:
                                print(f"[ERROR] Extrapolation for {device_address}-{field} failed → ZOH fallback. Reason: {e}")
                                last_val = df['value'].iloc[-1]
                                series.loc[target_extrap_index] = last_val
                                quality.loc[target_extrap_index] = "extrapolated"
                                method.loc[target_extrap_index] = "zoh-fallback"
                        else:
                            last_val = df['value'].iloc[-1]
                            series.loc[target_extrap_index] = last_val
                            quality.loc[target_extrap_index] = "extrapolated"
                            method.loc[target_extrap_index] = "zoh-insufficient-data"

                    else:
                        # ZOH for Door, Vibration
                        last_val = df['value'].iloc[-1]
                        series.loc[target_extrap_index] = last_val
                        quality.loc[target_extrap_index] = "extrapolated"
                        method.loc[target_extrap_index] = "zoh"
                if synchronization_mode == SynchronizationMode.PURE_QUALITY_STABILISATION:
                    # add real Data to Dataframe
                    for data in sensors[device_address].last_values:
                        series.loc[data["receive_time"]] = data[field]
                        quality.loc[data["receive_time"]] = "real_data"
                        method.loc[data["receive_time"]] = "real_data"
                    series.sort_index(inplace=True)
                    quality.sort_index(inplace=True)
                    method.sort_index(inplace=True)

                result = pd.concat([series, quality.rename("quality"), method.rename("method")], axis=1)

                #sync_df[field] = series
                #quality_df[field] = quality
                #method_df[field] = method

                synchronized_data[device_address][field] = result.to_dict("records")

        return synchronized_data
