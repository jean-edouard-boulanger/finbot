def sample_time_series(l, time_getter, frequency):
    next_date = time_getter(l[0])
    for item in l:
        current_time = time_getter(item)
        if current_time >= next_date:
            next_date = current_time + frequency
            yield item