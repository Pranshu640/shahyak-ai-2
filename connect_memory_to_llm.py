import os

from langchain_huggingface import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

# Step 1: Setup LLM (Mistral with HuggingFace)
# Get API token from environment variables
HF_TOKEN = os.environ.get("HF_TOKEN")
HUGGINGFACE_REPO_ID = os.environ.get("HUGGINGFACE_REPO_ID", "mistralai/Mistral-7B-Instruct-v0.3")

def load_llm(huggingface_repo_id):
    llm=HuggingFaceEndpoint(
        repo_id=huggingface_repo_id,
        task="text-generation",  # Specify the task explicitly
        temperature=0.5,
        max_new_tokens=512,
        huggingfacehub_api_token=HF_TOKEN,
    )
    return llm
# Step 2: Connect LLM with FAISS and Create chain

CUSTOM_PROMPT_TEMPLATE = """
You have to act as medical doctor and answer the following question based on the context provided.
firstly read the context and then answer the question.
in the end suggest a treatment for the patient based on the answer you provided.
Context: {context}
Question: {question}

Start the answer directly. No small talk please.
"""

def set_custom_prompt(custom_prompt_template):
    prompt=PromptTemplate(template=custom_prompt_template, input_variables=["context", "question"])
    return prompt

# Load Database
DB_FAISS_PATH="vectorstore/db_faiss"
embedding_model=HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
db=FAISS.load_local(DB_FAISS_PATH, embedding_model, allow_dangerous_deserialization=True)

# Create QA chain
qa_chain=RetrievalQA.from_chain_type(
    llm=load_llm(HUGGINGFACE_REPO_ID),
    chain_type="stuff",
    retriever=db.as_retriever(search_kwargs={'k':3}),
    return_source_documents=True,
    chain_type_kwargs={'prompt':set_custom_prompt(CUSTOM_PROMPT_TEMPLATE)}
)

# for i in range(10):
#     user_query=input("Write Query Here: ")
#     response=qa_chain.invoke({'query': user_query})

#     print("RESULT: ", response["result"])
    # print("SOURCE DOCUMENTS: ", response["source_documents"]) # Uncomment to see the source documents

# Define Rag function to be accessible when imported
def Rag(query):
    response=qa_chain.invoke({'query': query})
    return response["result"]

if __name__ == "__main__":
    # Test the Rag function with a sample query
    sample_query = input("Write Query Here: ")
    result = Rag(sample_query)
    print("RESULT: ", result)
