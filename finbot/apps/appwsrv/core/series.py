from finbot.apps.appwsrv import schema as appwsrv_schema


def order_series_by_last_value(
    series: list[appwsrv_schema.SeriesDescription],
) -> list[appwsrv_schema.SeriesDescription]:
    def key_getter(entry: appwsrv_schema.SeriesDescription) -> float:
        last_entry = entry.data[-1]
        return last_entry if last_entry is not None else 0.0

    return sorted(series, key=key_getter)
