def chunks(l, n):
    n = max(1, n)
    return (l[i:i+n] for i in range(0, len(l), n))


def estimate_time(filesize, page_count=None):
    '''
    Estimate processing time as
    one minute + 5 seconds per megabyte timeout
    '''
    return 60 + 5 * filesize / (1024 * 1024)
