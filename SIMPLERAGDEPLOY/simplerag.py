#!/usr/bin/env python
# coding: utf-8

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence



import os
import json


OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


#Load dos modelos (Embeddings e LLM)

embeddings_model = OpenAIEmbeddings()
llm = ChatOpenAI(model_name="gpt-3.5-turbo", max_tokens = 200)


def loadData():
#Carregar o PDF

    pdf_link = "Kanastra_Documentation.pdf"
    loader = PyPDFLoader(pdf_link, extract_images=False)
    pages = loader.load_and_split()

    #Separar em Chunks o documento

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 4000, #quanto menor o documento, menor pode ser o chunk para um retorno com mais agilidade, mas a recomendação é que nunca passe de 4 mil.
        chunk_overlap = 20,
        length_function = len,
        add_start_index = True
    )
    
    chunks = text_splitter.split_documents(pages)
    vectordb = Chroma.from_documents(chunks, embedding=embeddings_model)
    
    
    # Load Retriever
    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    return retriever

def getRelevantDocs(question): # função p recuperar documentos relevantes com base em uma (question) fornecida como entrada.
    retriever = loadData()
    context = retriever.invoke(question)
    return context

def ask(question, llm):
    TEMPLATE = """
    Você é um especialista em FDICs e fundos de investimentos. Responda a pergunta abaixo utilizando o contexto informado

    Contexto: {context}
    
    Pergunta: {question}
    """
    prompt = PromptTemplate(input_variables=["context", "question"], template=TEMPLATE)
    sequence = RunnableSequence(prompt | llm)
    context = getRelevantDocs(question)
    response = sequence.invoke({"context": context,"question": question})
    return response

def lambda_handler(event, context):
    body = json.loads(event.get("body", {}))
    query = body.get("question")
    response = ask(query, llm).content

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Tarefa Concluída com sucesso",
            "details": response,
        })
    }






