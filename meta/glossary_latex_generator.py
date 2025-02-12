
# term | definition | see1, see2...

raw_glossary_file = open("glossary_raw.txt", "r")
raw_glossary_lines = raw_glossary_file.readlines()
raw_glossary_file.close()

glossary = {}
references = {} # term : [term, term...]

for raw_line in raw_glossary_lines:
    line = raw_line.rstrip('\n')
    arg_list = line.split("|")
    if len(arg_list) < 2:
        #empty line or comment
        continue
    term = arg_list[0].rstrip(" ").lstrip(" ")
    definition = arg_list[1].rstrip(" ").lstrip(" ")
    glossary[term] = definition
    if len(arg_list) > 2:
        reference_list = arg_list[2].split(",")
        references[term] = []
        for ref in reference_list:
            references[term].append(ref.rstrip(" ").lstrip(" "))

glossary_keys = list(glossary.keys())

ordered_glossary_keys = sorted(glossary_keys)

result = ""

justify_text = True

glossary_file = open("glossary.tex", "w")
glossary_file.write("\\section{Glossary}\n")
glossary_file.write("{\\renewcommand{\\arraystretch}{0.5}\n \\begin{longtable}{ R{0.15\\linewidth}  L{0.81\\linewidth}  }\n\n")

for i in range(len(ordered_glossary_keys)):
    term = ordered_glossary_keys[i]
    endl = "\n"
    if i != len(ordered_glossary_keys) - 1:
        endl = "\\\\\n"
    refstr = ""
    if term in references.keys():
        refstr = " See " + ", ".join(f"\\hyperref[glossary:{x}]{{\\textbf{{{x}}}}}" for x in references[term]) + "."
    #result += f"\\textbf{{{term}}}\\rowlabel{{glossary:{term}}} & {glossary[term]}" + refstr + endl
    if justify_text:
        result += f"\\rowlabel{{glossary:{term}}} \\\\* \\textbf{{{term}}} & \\parbox[t]{{\\linewidth}}{{{glossary[term]}{refstr}}}" + endl
    else:
        result += f"\\rowlabel{{glossary:{term}}} \\\\* \\textbf{{{term}}} & {glossary[term]}" + refstr + endl

#print(result)

glossary_file.write(result)

glossary_file.write("\n\n\\end{longtable}}")

glossary_file.close()
