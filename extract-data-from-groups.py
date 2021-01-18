import re
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


if __name__ == "__main__":
    # log.info("Buscando numbers...")

    ppl_joined = {}
    ppl_left = {}
    numbers_joined = []
    numbers_left = []

    directory = sys.argv[1]
    count = 0
    for file in glob(os.path.join(directory, GLOB_STRING)):
        log.info(f"Extraindo números do arquivo {file}...")

        with zipfile.ZipFile(file) as archive:
            with archive.open("_chat.txt") as handle:
                for line in handle.read().decode().split("\n"):
                    line = line.strip()
                    number = line.split("+")[-1]

                    if "+" not in line:
                        continue

                    if line.endswith("left"):
                        date = line[1:9]
                        if date not in ppl_left:
                            ppl_left[date] = 0
                        ppl_left[date] += 1

                        number = "+{}".format(number.split("left")[0].strip())
                        number = number.strip()
                        if number not in numbers_left:
                            numbers_left.append(number)

                    if "joined using this group" in line:
                        date = line[1:9]
                        if date not in ppl_joined:
                            ppl_joined[date] = 0
                        ppl_joined[date] += 1

                        number = "+{}".format(number.split("joined")[0].strip())
                        number = number.strip()
                        if number not in numbers_joined:
                            numbers_joined.append(number)

total_ppl_joined = 0
total_ppl_left = 0

print()
for date in ppl_joined:
    print(f"-->> Dia {date}:")
    print(f"Pessoas que entraram: {ppl_joined[date]}")
    print(f"Pessoas que sairam: {ppl_left[date]}")
    print()

    total_ppl_joined += ppl_joined[date]
    total_ppl_left += ppl_left[date]

print()
print(f"Total de pessoas que entraram: {total_ppl_joined}")
print(f"Total de pessoas que sairam: {total_ppl_left}")
print(f"Total de pessoas remanescentes: {total_ppl_joined - total_ppl_left}")

print()
print("-->> Números:")
for number in numbers_joined:
    output = [re.sub("[^0-9]", "", number)]
    if number not in numbers_left:
        output.append("saiu")
    else:
        output.append("")

    output.append(datetime.now().strftime("%d/%m/%Y %H:%M"))
    print("\t".join(output))
