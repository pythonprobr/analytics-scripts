import os
import sys
from glob import glob

directory = sys.argv[1]
word_identifier = "joined"
output_file = "numbers.txt"

numbers = []
for file in glob(os.path.join(directory, "_cha*.txt")):
    with open(file) as handle:
        for line in handle:
            if word_identifier in line:
                line = line.strip()
                number = line.split("+")[-1]
                number = number.split(word_identifier)[0]
                number = number.replace("55", "").replace("‑", " ").strip()

                if number not in numbers:
                    numbers.append(number)

with open(output_file, "w") as handle:
    handle.write("\n".join(numbers))
    handle.write("\n")

print(f"Total numbers: {len(numbers)}")
print(f"Numbers are in {output_file}.")
