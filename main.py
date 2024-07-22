import streamlit as st
import pandas as pd
import numpy as np
import time
from tools import *
import json
import os
from io import BytesIO
from PyPDF2 import PdfReader

# from langchain_community.document_loaders import PyPDFLoader
# loader = PyPDFLoader("RajatSachdeva5y_6m.pdf")
# resume = loader.load()
# resume="\n".join(doc.page_content for doc in resume)

from langchain_community.document_loaders import PyPDFLoader
loader = PyPDFLoader("./JD/Draft_AI_LLM_Engineer.pdf")
jd = loader.load()
jd="\n".join(doc.page_content for doc in jd)

st.set_page_config(page_title="Technical Interview Round",layout="wide")

st.header("AI based tech interview round (graded from 1-5)", divider='orange')

QUERIES_KEY = 'queries'
RESPONSES_KEY = 'responses'
FLAGS_KEY = 'flags'
SCORES_KEY = 'scores'
USER_KEY = "user"
CHAT_KEY = "chat_history"
RESUME_KEY = "resume"

if CHAT_KEY not in st.session_state:
    if "temp" not in os.listdir():
        os.mkdir("./temp")
    with open("temp/chat_history.txt", 'w+') as file:
        pass
    st.session_state[CHAT_KEY]="initiated"

if USER_KEY not in st.session_state:
    name=False
    name=st.text_input("Enter you name to start !")
    with st.spinner("waiting for your response"):
        while not name:
            pass
    st.session_state[USER_KEY]=name

if RESUME_KEY not in st.session_state:    
    resume_pdf=False
    resume_pdf = st.file_uploader("Please upload your resume (in pdf format)", type=["pdf"])
    with st.spinner("upload resume to continue !"):
        while not resume_pdf:
            pass
    with st.spinner("Analyzing your resume..."):
        pdf_bytes = resume_pdf.read()
        pdf_stream = BytesIO(pdf_bytes)
            
            # Create a PDF reader object
        pdf_reader = PdfReader(pdf_stream)
        num_pages = len(pdf_reader.pages)
        resume = ""

        for page_num in range(num_pages):
            page = pdf_reader.pages[page_num]
            resume += page.extract_text() + "\n"


        st.session_state[RESUME_KEY] = resume
else:
    resume=st.session_state[RESUME_KEY]


if QUERIES_KEY not in st.session_state:
    st.session_state[QUERIES_KEY] = []

if RESPONSES_KEY not in st.session_state:
    st.session_state[RESPONSES_KEY] = []

if FLAGS_KEY not in st.session_state:
    st.session_state[FLAGS_KEY] = {"take_decision": True, "ask_question": False, "user_input": False, "report": False, "end": False}

if SCORES_KEY not in st.session_state:
    st.session_state[SCORES_KEY] = {"Relevance": [], "Accuracy": [], "Clarity": [], "Depth": [], "Language Use": [], "Completeness": []}

if len(st.session_state[RESPONSES_KEY]):
    st.write("interview history")
    with st.container(height=None,border=True):
        for query, response in zip(st.session_state[QUERIES_KEY], st.session_state[RESPONSES_KEY]):
            with st.chat_message("assistant"):
                st.write(query)
            with st.chat_message("user"):
                st.write(response)

    st.markdown("##")

if (USER_KEY in st.session_state) and (CHAT_KEY in st.session_state):

    while True:

        with open("./temp/chat_history.txt","r+") as file:
            chat_history=file.read()

        if st.session_state[FLAGS_KEY]["take_decision"]:
            print("decision node")
            decision=supervisor(jd,resume,chat_history)
            print("decision:",decision)
            if decision == 'ask':
                st.session_state[FLAGS_KEY]["ask_question"]=True

            else:
                print("Interview ended.")

                st.warning("End of your interview !")

                with st.spinner("saving your responses"):
                    store_history(tool_input={'interview_doc':chat_history,'candidate':st.session_state[USER_KEY]})

                cumulative_score=0

                with st.spinner("getting you performance score !"):
                    for i in st.session_state[SCORES_KEY]:
                        print(st.session_state[SCORES_KEY][i])
                        st.session_state[SCORES_KEY][i]=sum(st.session_state[SCORES_KEY][i])/len(st.session_state[SCORES_KEY][i])
                        cumulative_score+=st.session_state[SCORES_KEY][i]
                    cumulative_score/=len(st.session_state[SCORES_KEY])
                    cumulative_score=str(round(cumulative_score,2))

                    df_temp=pd.DataFrame(st.session_state[SCORES_KEY].items(), columns=['Criteria', 'Score'])
                    df_temp.to_csv(f"reports/{st.session_state[USER_KEY]}.csv",index=False)
                          
                    with st.chat_message("admin",avatar="😒"):
                        st.write("Your Interview Score (1-5) is: ", cumulative_score)
                print("Score:",cumulative_score)

                st.session_state[FLAGS_KEY]["take_decision"]=False
                st.stop()
                

            st.session_state[FLAGS_KEY]["take_decision"]=False



        if st.session_state[FLAGS_KEY]["ask_question"]:
            print("question gen node")
            with st.spinner("generating question"):
                question = ask_question(tool_input={'resume':resume, 'jd':jd, 'chat_history':chat_history})
            st.session_state[QUERIES_KEY].append(question)
            with st.chat_message("assistant"):
                st.write(question)
            st.session_state[FLAGS_KEY]["user_input"]=True
            st.session_state[FLAGS_KEY]["ask_question"]=False
            with open("./temp/chat_history.txt","a+") as file:
                file.writelines(f"\nInterviewer: {question} \n")
            print(f"\nInterviewer: {question} \n\n")

        if st.session_state[FLAGS_KEY]["user_input"]:
            placeholder = st.empty()
            print("human input node")
            candidate_response=False
            with placeholder:
                candidate_response = st.text_input(f"{st.session_state[USER_KEY]}: ",key=len(st.session_state[RESPONSES_KEY]))
            with st.spinner("waiting for your response"):
                while not candidate_response:
                    pass
            if candidate_response:
                placeholder.empty()
                st.session_state[RESPONSES_KEY].append(candidate_response)
                with open("./temp/chat_history.txt","a+") as file:
                    file.writelines(f"\nCandidate: {candidate_response}\n\n")
                print(f"\nCandidate: {candidate_response} \n\n")
                st.session_state[FLAGS_KEY]["report"]=True
                st.session_state[FLAGS_KEY]["user_input"]=False

        if st.session_state[FLAGS_KEY]["report"]:
            print("answer evaluation node")
            with st.spinner("evaluating your last response"):
                score=get_report(tool_input={'questions':st.session_state[QUERIES_KEY][-1],'responses':st.session_state[RESPONSES_KEY][-1],'resume':resume,'jd':jd})

            candidate_response=""

            from io import StringIO
            score_csv = StringIO(score)
            temp_df=pd.read_csv(score_csv,header=None)
            result_dict = temp_df.set_index(0).to_dict()[1]
            for i in list(result_dict.keys()):
                if i in st.session_state[SCORES_KEY]:
                    st.session_state[SCORES_KEY][i].append(result_dict[i])


            st.session_state[FLAGS_KEY]["report"]=False
            st.session_state[FLAGS_KEY]["take_decision"]=True
