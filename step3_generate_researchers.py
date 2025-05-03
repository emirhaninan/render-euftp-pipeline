import pandas as pd
from bs4 import BeautifulSoup
import requests
import re
# step1_generate_calls.py
def run():
    # your logic here

# etc for the other steps
#BİLGİ's website. Code will start to get specific to the job now
    html_text = requests.get("https://www.bilgi.edu.tr/en/research/researchers/").text

    soup = BeautifulSoup(html_text, 'html.parser')

    first_names = []
    last_names = []
    full_names = []
    faculties = []
    research_interests_all = []

    rows = soup.find_all('tr')

    for row in rows:
        cells = row.find_all('td')
        if cells:
            first_name = cells[0].get_text().strip()
            last_name = cells[1].get_text().strip()
            faculty = cells[2].get_text().strip()
            
            #clean research interests: replace \r\n, fix "ı" to "i", and reduce extra spaces
            raw_interests = cells[3].get_text().replace('\r\n', ' ').replace('ı', 'i').strip().lower()
            research_interests = [
                re.sub(r'\s+', ' ', re.sub(r'\b(and|the|&|-|of|to|in|for|as|at)\b', '', interest.strip()))
                for interest in raw_interests.split(',')
            ]
            research_interests = list(filter(None, set(research_interests)))

            full_names.append(first_name + " " + last_name)
            faculties.append(faculty)
            research_interests_all.append(research_interests)

    data = {
        'Full Name': full_names,
        'Faculty': faculties,
        'Research Interests': research_interests_all
    }

    df = pd.DataFrame(data)
    df.to_csv('researchers_data.csv', index=False)
    df.to_excel('researchers_data.xlsx', index=False)
    print("CSV and Excel files have been created successfully.")

if __name__ == "__main__":
    run()