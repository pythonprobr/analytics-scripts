from datetime import datetime
import sys
import csv

filename = sys.argv[1]

count = 0
new_file = [
    [
        "Email",
        "Phone",
        "First Name",
        "Last Name",
        "Country",
        "Zip",
    ]
]

index = 0
with open(filename) as handle:
    content = handle.read()
    if "Nome do segmento" in content:
        index += 1

with open(filename) as handle:
    for line in csv.reader(handle):
        count += 1
        if count > 1:
            email = line[index + 1]
            name = line[index + 2]
            new_file.append([email, "", name, "", "", ""])

new_filename = "/Users/moa/Downloads/list-{}.csv".format(
    datetime.now().strftime("%Y-%m-%d-%H-%M")
)
with open(new_filename, "w") as handle:
    writer = csv.writer(handle)
    for item in new_file:
        writer.writerow(item)

print(new_filename)