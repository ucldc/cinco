import os
import json

report_dir = "/Users/bhui/dev/cinco/ead_relative_links"
aggregated = {}
total_listed = 0
seen = set()
duplicates = []
total_hrefs = 0
report_filenames = os.listdir(report_dir)
for report_filename in report_filenames:
    with open(f"{report_dir}/{report_filename}", "r") as f:
        content = f.read()
        content = json.loads(content)
        page_ead_count = len(content)
        total_listed += page_ead_count
        for s3_key in content:
            if s3_key in seen:
                duplicates.append(s3_key)
                print(f"Duplicate: {report_filename}")
            else:
                seen.add(s3_key)
        page_href_count = 0
        for ead_filename in content:
            page_href_count += len(content[ead_filename]["cinco_hrefs"])
        total_hrefs += page_href_count
        print(f"{report_filename} {page_ead_count} {page_href_count}")

        aggregated.update(content)

print(f"Total listed s3 files: {total_listed}")
print(f"Total aggregated eads: {len(aggregated)}")
print(f"Duplicates: {json.dumps(duplicates)}")
print(f"Total hrefs in report: {total_hrefs}")

with open("eads_with_unexpanded_otherfindaid_links.json", "w") as f:
    f.write(json.dumps(dict(sorted(aggregated.items()))))