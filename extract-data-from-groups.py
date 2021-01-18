import os
import sys
import zipfile
from datetime import datetime, timedelta
from glob import glob

from activecampaign.client import Client

from flatten_dict import flatten
from resources.gsheets import spreadsheet
from resources.active_campaign import client
from utils import log
from settings import TIME_ZONE

GLOB_STRING = "*#*.zip"


if __name__ == '__main__':
    # log.info("Buscando numbers...")

    ppl_joined = {}
    ppl_left = {}

    directory = sys.argv[1]
    count = 0
    for file in glob(os.path.join(directory, GLOB_STRING)):
        log.info(f"Extraindo números do arquivo {file}...")

        with zipfile.ZipFile(file) as archive:
            with archive.open("_chat.txt") as handle:
                for line in handle.read().decode().split("\n"):
                    line = line.strip()
                    
                    if line.endswith('left'):
                        date = line[1:9]
                        if date not in ppl_left:
                            ppl_left[date] = 0
                        ppl_left[date] += 1
                    
                    if 'joined using this group' in line:
                        date = line[1:9]
                        if date not in ppl_joined:
                            ppl_joined[date] = 0
                        ppl_joined[date] += 1

total_ppl_joined = 0
total_ppl_left = 0

print()
for date in ppl_joined:
    print(f'-->> Dia {date}:')
    print(f'Pessoas que entraram: {ppl_joined[date]}')
    print(f'Pessoas que sairam: {ppl_left[date]}')
    print()

    total_ppl_joined += ppl_joined[date]
    total_ppl_left += ppl_left[date]

print()
print(f'Total de pessoas que entraram: {total_ppl_joined}')
print(f'Total de pessoas que sairam: {total_ppl_left}')
print(f'Total de pessoas remanescentes: {total_ppl_joined - total_ppl_left}')
