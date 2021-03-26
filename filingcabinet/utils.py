def chunks(li, n):
    n = max(1, n)
    return (li[i:i+n] for i in range(0, len(li), n))


def estimate_time(filesize, page_count=None):
    '''
    Estimate processing time as
    one minute + 5 seconds per megabyte timeout
    '''
    return int(60 + 5 * filesize / (1024 * 1024))
