import logging

formatter = logging.Formatter("[%(asctime)s][%(filename)s][%(levelname)s] %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)

log = logging.getLogger("tasks")
log.setLevel(logging.DEBUG)
log.addHandler(ch)
