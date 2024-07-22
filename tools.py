from langchain.tools import tool
import os

@tool
def store_history(interview_doc:str, candidate:str) -> str:
    """
    Download the chat history on the system
    """

    # function definition starts from here

    directories=os.listdir()
    if 'interview' not in directories:
        os.mkdir('interview')

    file_path=f"interview/{candidate}.txt"

    with open(file_path,'w+') as file:
        file.writelines(interview_doc)

    return file_path


from langchain.tools import tool
from dotenv import load_dotenv
from openai import AzureOpenAI
import pandas as pd
import os

load_dotenv()


@tool
def get_report(questions: str, responses: str, resume: str, jd: str) -> str:
    """
    Test the interview chat against a benchmark and store the report 
    """

    rubrics=pd.read_csv("eval_rubrics.csv")

    # function definition starts here

    client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_4o_API_KEY"),  
    api_version = os.getenv("API_VERSION_4o"),
    azure_endpoint = os.getenv("AZURE_OPENAI_4o_ENDPOINT")
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"""You are a corporate interviewer responsible for grading the candidates according to their responses \
             This is the criterian for evaluation: {rubrics}. \
             This is the candidate's resume: {resume}. \
             This is the job description: {jd}. \
             Question asked from the candidate: {questions}. \
             Response given by the candidate: {responses}. \
             Perform strict grading from 5 according to the answer's relevance to the question and alignment with resume and job description. \
             Give 1 for derogatory, irrrelevant and one word answers. \
             Just give the scores without explaination under each criteria according to the relevance to the job. \
             Give answer in the following format: Relevance,relevance_score,1\nAccuracy,accuracy_score,1\nClarity,clarity_score,1\nDepth,depth_score,1\nLanguage Use,language_score,1\nCompleteness,completeness_score,1
 """}])

    score=response.choices[0].message.content
    # score=score.replace(',',':')

    return score

            #  This is the candidate's resume: {resume}. \
            #  This is the job description: {jd}. \



import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from langchain.tools import tool

load_dotenv()

@tool
def ask_question(resume:str, jd:str, chat_history:str) -> str:
    """
    LLM for generating a new question to be asked from the candidate
    """

    # function definition starts here

    client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_4o_API_KEY"),  
    api_version = os.getenv("API_VERSION_4o"),
    azure_endpoint = os.getenv("AZURE_OPENAI_4o_ENDPOINT")
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"""You are a corporate interviewer responsible for taking candidate interviews. \
             This is a technical round, hence you need to ask questions regarding relevant technologies. \
             You may ask some short syntax or a conceptual question. \
             This is the job description: {jd}. \
             This is the candidate's resume: {resume}. \
             This is the past interaction you had with the candidate: {chat_history}. \
             Either ask a review question on candidate's last reponse or ask a new question. \
             Make sure to only ask a single question. \
             The question needs to be relevant to the job description or the candidate's past experience."""}])

    question=response.choices[0].message.content

    return question


def supervisor(jd,resume,chat_history):

    client = AzureOpenAI(
    api_key = os.getenv("AZURE_OPENAI_4o_API_KEY"),  
    api_version = os.getenv("API_VERSION_4o"),
    azure_endpoint = os.getenv("AZURE_OPENAI_4o_ENDPOINT")
    )
        
    decision = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": f"""
                You are a corporate interviewer responsible for taking candidate interviews. Decide whether to ask another question or end the conversation.
                This is the job description: {jd}.
                This is the candidate's resume: {resume}.
                This is the past interaction you had with the candidate: {chat_history}.
                Respond with 'ask' to ask another question or 'end' to end the conversation.
                """}]).choices[0].message.content
    
    return decision