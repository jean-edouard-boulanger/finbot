def sample_time_series(l, time_getter, frequency):
    next_date = time_getter(l[0])
    if not l:
        return
    yield l[0]
    if len(l) < 2:
        return
    for item in l[1:-1]:
        current_time = time_getter(item)
        if current_time >= next_date:
            next_date = current_time + frequency
            yield item
    yield l[-1]
