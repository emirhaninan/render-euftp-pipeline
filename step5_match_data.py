import pandas as pd
import ast
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import numpy as np
# step1_generate_calls.py
def run():
    # your logic here

# etc for the other steps
    #load both files
    researchers_path = 'researchers_data.xlsx'
    calls_path = '5-SentenceTransformerResultsforCalls.xlsx'
    researchers_df = pd.read_excel(researchers_path)
    calls_df = pd.read_excel(calls_path)

    researcher_col_name = 'Research Interests'  #keywords column in researchers_data.xlsx
    call_col_name = 'All Keywords'  #keywords column in 5-SentenceTransformerResultsforCalls.xlsx

    researchers_df['Processed Keywords'] = researchers_df[researcher_col_name].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )
    calls_df['Processed Call Keywords'] = calls_df[call_col_name].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else x
    )

    researcher_keywords_list = [' '.join(keywords) for keywords in researchers_df['Processed Keywords']]
    call_keywords_list = [' '.join(keywords) for keywords in calls_df['Processed Call Keywords']]

    vectorizer = TfidfVectorizer()
    all_keywords = researcher_keywords_list + call_keywords_list
    tfidf_matrix = vectorizer.fit_transform(all_keywords)

    researcher_tfidf = tfidf_matrix[:len(researcher_keywords_list)]
    call_tfidf = tfidf_matrix[len(researcher_keywords_list):]

    model = SentenceTransformer('all-MiniLM-L6-v2')

    researcher_embeddings = model.encode(researcher_keywords_list)
    call_embeddings = model.encode(call_keywords_list)

    final_assignments = []

    #######assign calls to researchers based on hybrid similarity (TF-IDF + Semantic)
    for i, researcher_vector in enumerate(researcher_tfidf):
        tfidf_similarity_scores = cosine_similarity(researcher_vector, call_tfidf).flatten()
        
        semantic_similarity_scores = util.cos_sim(researcher_embeddings[i].reshape(1, -1), call_embeddings).flatten()
        
        if tfidf_similarity_scores.shape != semantic_similarity_scores.shape:
            raise ValueError("TF-IDF and semantic similarity scores must have the same shape.")
        
        #combine scores (weighted average) HYBRID APPROACH
        combined_scores = 0.7 * tfidf_similarity_scores + 0.3 * semantic_similarity_scores.numpy()
        
        matched_indices = np.where(combined_scores > 0.09)[0]  #adjust threshold as needed. incremental adjustments bring big results. be careful
        for idx in matched_indices:
            assignment = {
                'Full Name': researchers_df.iloc[i]['Full Name'],
                'Research Interests': researchers_df.iloc[i][researcher_col_name],
                'Assigned Call': calls_df.iloc[idx]['Project Name'],
                'Deadline': calls_df.iloc[idx]['Deadline'], 
                'URL': calls_df.iloc[idx]['URL']  
            }
            final_assignments.append(assignment)

    assignments_df = pd.DataFrame(final_assignments)

    output_file_path = 'Researcher_Assigned_Calls_With_Deadline_URL.xlsx'
    assignments_df.to_excel(output_file_path, index=False)

    print(f"Call assignment results have been saved to '{output_file_path}'")



if __name__ == "__main__":
    run()