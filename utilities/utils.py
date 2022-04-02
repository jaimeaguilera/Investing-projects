from datetime import datetime

def timestamp(fmt="%Y%m%d%H%M"):
    return datetime.utcnow().strftime(fmt)