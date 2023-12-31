import pandas as pd
import numpy as np
import streamlit as st
from io import BytesIO
import click
import spacy
import docx2txt
import pdfplumber
from pickle import load
import requests
import re
import os
import sklearn
import PyPDF2
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('omw-1.4')
# load pre-trained model
import en_core_web_sm
nlp = en_core_web_sm.load()
from nltk.tokenize import RegexpTokenizer
from nltk import word_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords
import matplotlib.pyplot  as plt
stop=set(stopwords.words('english'))
from spacy.matcher import Matcher
# initialize matcher with a vocab
matcher = Matcher(nlp.vocab)
import joblib





mfile = '/content/drive/MyDrive/Resume_Classification_NLP/word_vectorizer.pkl'
model = joblib.load(mfile)
mfile1 = '/content/drive/MyDrive/Resume_Classification_NLP/SVM_model.pkl'
model1 = joblib.load(mfile1)

def add_bg_image():
    st.markdown(
          f"""
          <style>
         .stApp {{
             background-image: url("https://img.freepik.com/free-vector/abstract-background-with-squares_23-2148995948.jpg?w=996&t=st=1663219978~exp=1663220578~hmac=aee3da925492e169a7f9fb7d1aa1577c58a7db3849d8be3f448114080d42a7a7");
             background-attachment: fixed;
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True)
     
add_bg_image()

def extract_skills(resume_text):

    nlp_text = nlp(resume_text)
    noun_chunks = nlp_text.noun_chunks

    # removing stop words and implementing word tokenization
    tokens = [token.text for token in nlp_text if not token.is_stop]
            
    # reading the csv file
    data = pd.read_csv("/content/drive/MyDrive/Resume_Classification_NLP/skills.csv") 
            
    # extract values
    skills = list(data.columns.values)
            
    skillset = []
            
    # check for one-grams (example: python)
    for token in tokens:
        if token.lower() in skills:
            skillset.append(token)
            
    # check for bi-grams and tri-grams (example: machine learning)
    for token in noun_chunks:
        token = token.text.lower().strip()
        if token in skills:
            skillset.append(token)
            
    return [i.capitalize() for i in set([i.lower() for i in skillset])]

# Function to extract text from resume
def getText(filename):
    fullText = ''

    if filename.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        doc = docx2txt.process(filename)
        
        for para in doc:
            fullText = fullText + para
           
    else:  
        with pdfplumber.open(filename) as pdf_file:
            pdoc = PyPDF2.PdfReader(filename)
            number_of_pages = len(pdoc.pages)
            page_content = pdoc.pages[0].extract_text()
             
        for paragraph in page_content:
            fullText =  fullText + paragraph
         
    return fullText

def display(doc_file):
    resume = []
    if doc_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        resume.append(docx2txt.process(doc_file))

    else:
        with pdfplumber.open(doc_file) as pdf:
            pages=pdf.pages[0]
            resume.append(pages.extract_text())
            
    return resume

def preprocess(sentence):
    sentence=str(sentence)
    sentence = sentence.lower()
    sentence=sentence.replace('{html}',"") 
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', sentence)
    rem_url=re.sub(r'http\S+', '',cleantext)
    rem_num = re.sub('[0-9]+', '', rem_url)
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(rem_num)  
    filtered_words = [w for w in tokens if len(w) > 2 if not w in stopwords.words('english')]
    lemmatizer = WordNetLemmatizer()
    lemma_words=[lemmatizer.lemmatize(w) for w in filtered_words]
    return " ".join(lemma_words)  


# Function to extract experience details
def expDetails(Text):
    global sent
   
    Text = Text.split()
   
    for i in range(len(Text)-2):
        Text[i].lower()
        
        if Text[i] ==  'years':
            sent =  Text[i-2] + ' ' + Text[i-1] +' ' + Text[i] +' '+ Text[i+1] +' ' + Text[i+2]
            l = re.findall(r'\d*\.?\d+',sent)
            for i in l:
                a = float(i)
            return(a)
            return (sent)

target = {0:'Peoplesoft',1:'SQL Developer',2:'React JS Developer',3:'Workday'}

def main():
    html_temp = """
    <div style ="background-color:transparent;padding:13px;color:black">
    <h1 style ="color:black;text-align:center;"> RESUME CLASSIFICATION </h1>
    </div>
    """
    st.markdown(html_temp, unsafe_allow_html = True)

    file_type=pd.DataFrame([], columns=['Uploaded File', 'Experience', 'Skills', 'Predicted Profile'])
    filename = []
    predicted = []
    experience = []
    skills = []

    upload_file = st.file_uploader('Hey,Upload Your Resumes ',
                                type= ['docx','pdf'],accept_multiple_files=True)

    for doc_file in upload_file:
            if doc_file is not None:
                filename.append(doc_file.name)
                cleaned=preprocess(display(doc_file))
                # Transform the preprocessed text using model1 (TfidfVectorizer)
                transformed_text = model.transform([cleaned])
                # Predict the class using the classification model
                prediction = model1.predict(transformed_text)[0]

                #prediction = model.predict(model1.transform([cleaned]))[0]
                predicted.append(target.get(prediction))
                extText = getText(doc_file)
                exp = expDetails(extText)
                experience.append(exp)
                skills.append(extract_skills(extText))
    if len(predicted) > 0:
        file_type['Uploaded File'] = filename
        file_type['Experience'] = experience
        file_type['Skills'] = skills
        file_type['Predicted Profile'] = predicted
        # file_type
        # Custom formatting

        formatted_file_type = file_type.copy()
        formatted_file_type['Experience'] = formatted_file_type['Experience'].apply(lambda x: '<span style="color: red;">{:.1f}</span>'.format(x) if x is not None else '')
        st.table(formatted_file_type)

        #formatted_file_type['Experience'] = formatted_file_type['Experience'].apply(lambda x: '{:.1f}'.format(x) if x is not None else '')
        #st.table(formatted_file_type)


    st.markdown('<p style="color: blue;">*Note: Classifies only for Workday, Peoplesoft, React JS and SQL Developer Resumes</p>', unsafe_allow_html=True)

if __name__ == '__main__':
     main()
