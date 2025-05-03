import csv
import json
import requests
import pandas as pd
from datetime import datetime
from nltk.corpus import stopwords
import re
import nltk

def run():
    nltk.download('stopwords')
    stop_words = set(stopwords.words('english'))
#appending frequently seen keywords. this is disregardable
    def keywordQuery(content):
        keyword_map = {
            "MSCA": ["PhD", "Doctoral", "post-doc", "postdoctoral", "R&I", "interdisciplinary", "mobility", "innovation"],
            "Marie": ["PhD", "Doctoral", "post-doc", "postdoctoral", "R&I", "interdisciplinary", "mobility", "innovation"],
            "Social": ["Social"],
            "Innovation": ["Innovation"],
            "Transition": ["Technology", "business", "market", "commercial"],
            "Chips": ["microelectronics", "chips", "technology", "software", "AI", "semiconductor", "innovation", "future", "automotive", "industry"],
            "Vehicle": ["microelectronics", "chips", "technology", "software", "AI", "semiconductor", "innovation", "future", "automotive", "industry"],
            "SRIA": ["microelectronics", "chips", "technology", "software", "AI", "semiconductor", "innovation", "future", "automotive", "industry"],
            "Processors": ["microelectronics", "chips", "technology", "software", "AI", "semiconductor", "innovation", "future", "automotive", "industry"],
            "Korea": ["microelectronics", "chips", "technology", "software", "AI", "semiconductor", "innovation", "future", "automotive", "industry"],
            "Software": ["Software", "technology", "innovation"],
            "EIC": ["deep tech", "patient capital", "research", "innovation", "technology", "EIC"],
            "greener": ["eco-friendly", "sustainability", "ecology", "carbon footprint", "Green Deal"],
            "ERA": ["R&I", "innovation", "technology", "Widening Countries"],
            "Hop": ["R&I", "innovation", "technology", "Widening Countries"],
            "Researchers'": ["Research", "academia"],
            "International": ["International"],
            "European": ["sustainable", "eco", "ecosystem", "urban", "society", "climate change", "EU Missions"]
        }
        
        keywords = []
        for word in content.replace("-", " ").split():
            keywords.extend(keyword_map.get(word, []))
        return keywords

    #time formatting
    def formatTime(date_time_str):
        return datetime.strptime(date_time_str.split('T')[0], "%Y-%m-%d").strftime("%d %m %Y")

    def extract_last_part(url):
        return url.rsplit("/", 1)[-1]

    #url formatting should not be tinkered with. some calls only open externally by the specific url appendages below
    def modify_url(url):
        base_url = "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/"
        last_part = extract_last_part(url)
        
        if last_part.endswith(".json"):
            last_part = "topic-details/" + last_part[:-5]
        else:
            last_part = "competitive-calls-cs/" + ''.join(c for c in last_part if c.isdigit())
        last_part = last_part.lower()
        modified_url = base_url + last_part
        return modified_url

    #api for the european commission funding & tenders portal
    api_url = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
    params = {"apiKey": "SEDIA", "text": "***", "pageSize": "50", "pageNumber": "1"}
    query = {
        "bool": {
            "must": [
                #type 8 was added recently. need to manually check if new types are added, not to omit any data
                {"terms": {"type": ["1", "2", "0", "8"]}},
                #only looking for horizon calls
                {"terms": {"status": ["31094502", "31094501"]}},
                {"term": {"programmePeriod": "2021 - 2027"}},
                {"terms": {"frameworkProgramme": ["43108390"]}}
            ]
        }
    }
    languages = ["en"]
    sort = {"field": "sortStatus", "order": "ASC"}


    data_list = []
    page = 1
    while True:
        params["pageNumber"] = str(page)
        response = requests.post(
            api_url,
            params=params,
            files={
                "query": ("blob", json.dumps(query), "application/json"),
                "languages": ("blob", json.dumps(languages), "application/json"),
                "sort": ("blob", json.dumps(sort), "application/json"),
            },
        )

        data = response.json()
        if "results" not in data or not data["results"]:
            break

        for result in data["results"]:
            content = result.get("content", "")
            metadata = result.get("metadata", {})
            
            keywords = metadata.get("keywords", [])
            keywords = keywords if isinstance(keywords, list) else [keywords]
            keywords.extend(keywordQuery(content))

            data_list.append([
                content,
                metadata.get("projectName", ""),
                metadata.get("title", ""),
                metadata.get("callTitle", ""),
                metadata.get("tags", ""),
                keywords,
                formatTime(metadata.get("startDate", [""])[0]),
                formatTime(metadata.get("deadlineDate", [""])[-1]),
                modify_url(result.get("url", ""))
            ])
        #this is a way to abort the program when the calls are finished
        if len(data["results"]) < 50:
            break
        page += 1

    #csv not required but done anyway
    csv_file = "calls_description.csv"
    with open(csv_file, "w", newline="", encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Project Name", "announcementSummary", "title", "callTitle", "tags", "Keywords", "Beginning", "Deadline", "URL"])
        writer.writerows(data_list)

    excel_file = "Calls_description_combined.xlsx"
    df = pd.read_csv(csv_file)
    df.to_excel(excel_file, index=False)

    #getting as many data for keywords as possible. sometimes keywords backend data is empty so need to check other info
    columns_to_combine = ['title', 'callTitle', 'tags', 'announcementSummary', 'Keywords']
    def combine_columns(row):
        combined = []
        for col in columns_to_combine:
            if col in row and pd.notna(row[col]):
                value = row[col]
                if isinstance(value, str) and value.startswith('['):
                    combined.extend(value.strip('[]').replace("'", "").split(','))
                else:
                    combined.append(str(value).strip())
        return ', '.join(map(str.strip, combined)).lower()



    

    

    #function to clean and join phrases with underscores for fasttext. not required anymore
    def clean_and_join_phrases(text):
        cleaned_text = re.sub(r'[^a-zA-Z\s]', '', text)
        phrases = cleaned_text.split()
        filtered_phrases = [phrase.lower() for phrase in phrases if phrase.lower() not in stop_words]
        return [filtered_phrases[i] + " " + filtered_phrases[i + 1] for i in range(len(filtered_phrases) - 1)] if len(filtered_phrases) > 1 else filtered_phrases

    def combine_and_clean(row):
        combined = []
        for col in columns_to_combine:
            if col in row and pd.notna(row[col]):
                value = row[col]
                if isinstance(value, str) and value.startswith('['):
                    items = value.strip('[]').replace("'", "").split(',')
                    combined.extend(map(str.strip, items))
                else:
                    combined.append(str(value).strip())
        combined_text = ' '.join(combined)
        return clean_and_join_phrases(combined_text)

    columns_to_combine = ['title', 'callTitle', 'tags', 'announcementSummary', 'Keywords']

    df['Combined Keywords'] = df.apply(combine_and_clean, axis=1)

    df.drop(columns=columns_to_combine, inplace=True, errors='ignore')

    new_file_path = 'NOHYPHENSingleColumnCALLS_WithArrays.xlsx'
    df.to_excel(new_file_path, index=False)

    print("Cleaned and formatted Excel file created with arrays of phrases:", new_file_path)

if __name__ == "__main__":
    run()

