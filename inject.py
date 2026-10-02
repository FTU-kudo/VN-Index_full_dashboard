with open("dashboard/js/app.js", "r", encoding="utf-8") as f:
    lines = f.readlines()

with open("dashboard/js/echarts_snippet.js", "r", encoding="utf-8") as f:
    snippet = f.read()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "function renderFinancialCharts()" in line:
        start_idx = i - 3 # include comments
    if start_idx != -1 and "function formatNumber(" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_lines = lines[:start_idx] + [snippet + "\n\n"] + lines[end_idx:]
    with open("dashboard/js/app.js", "w", encoding="utf-8") as f:
        f.writelines(new_lines)
    print("Replaced successfully.")
else:
    print("Could not find bounds.")
