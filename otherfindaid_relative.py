import boto3
import json
import xml.etree.ElementTree as ET

s3_client = boto3.client("s3")
paginator = s3_client.get_paginator('list_objects_v2')

s3_page = 0
for page in paginator.paginate(Bucket='cinco-prd', Prefix='media/ead'):
    print(f"\n# s3 page: {s3_page}")
    eads_with_extrefs = {}
    if 'Contents' in page:
        for obj in page['Contents']:
            key = obj['Key']
            filename = key.split("/")[-1]

            response = s3_client.get_object(Bucket="cinco-prd", Key=f"media/ead/{filename}")
            # print(f"{key=}")
            file_content = response['Body'].read().decode('utf-8', 'ignore')
            root = ET.fromstring(file_content)
            parent_map = {child: parent for parent in root.iter() for child in parent}

            hrefs = []
            for otherfindaid in root.iter("otherfindaid"):
                parent_node = parent_map.get(otherfindaid)
                unittitle_nodes = [title for title in parent_node.iter('unittitle')]
                if unittitle_nodes:
                    unittitle = unittitle_nodes[0].text
                else:
                    unittitle = None
                for extref in  otherfindaid.iter("extref"):
                    for attrib_name in extref.attrib:
                        if attrib_name.endswith("href"):
                            hrefs.append(
                                {
                                    "parent_tag": parent_node.tag,
                                    "unittitle": unittitle,
                                    "href": extref.attrib[attrib_name]
                                }
                            )

            for href in hrefs:
                href = href["href"]
                if href == None:
                    print(f"**** {filename} has href of None: {hrefs}")
                elif not href.startswith("http"):
                    eads_with_extrefs[filename] = {
                        "cinco_hrefs": hrefs
                    }
                    print(filename, len(hrefs))

                    break

        if eads_with_extrefs:
            with open(f"ead_relative_links/{s3_page}.json", "w") as f:
                f.write(json.dumps(eads_with_extrefs))

    s3_page += 1


