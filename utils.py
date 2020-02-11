import logging

formatter = logging.Formatter("%(asctime)s|%(levelname)s|%(filename)s| %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)

log = logging.getLogger("tasks")
log.setLevel(logging.DEBUG)
log.addHandler(ch)
