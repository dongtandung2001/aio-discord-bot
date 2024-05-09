from PyPDF2 import PdfReader
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings

from chromadb import PersistentClient

from dotenv import load_dotenv

load_dotenv()


def get_pdf_text(pdf):
    text = ""

    pdf_reader = PdfReader(pdf)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)

    chunks = text_splitter.split_text(text)
    return chunks


def get_vector_store(text_chunks):
    embedding2 = OpenAIEmbeddings()
    # vector_store = faiss.FAISS.from_texts(text_chunks, embedding=embeddings)
    # vector_store.save_local("faiss_index")

    vector_db = Chroma.from_texts(
        text_chunks,
        embedding=embedding2,
        persist_directory="./data",
        collection_name="abc",
        collection_metadata={"id": "id"},
    )
    vector_db.persist()
    return vector_db


def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
    provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:

    """
    model2 = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    chain = load_qa_chain(model2, chain_type="stuff", prompt=prompt)

    return chain


def get_answer(question):
    embedding2 = OpenAIEmbeddings()

    db = Chroma(
        persist_directory="./data",
        embedding_function=embedding2,
        collection_name="abc",
        collection_metadata={"id": "id"},
    )

    docs = db.similarity_search(question, k=1)

    chain = get_conversational_chain()

    response = chain.invoke(
        {"input_documents": docs, "question": question}, return_only_outputs=True
    )

    return response


# pdf = "transcript.pdf"
# raw_text = get_pdf_text(pdf)
# text_chunks = get_text_chunks(raw_text)
# get_vector_store(text_chunks)


# a = get_answer("what happened in Fall semester 2021 and summarize score")
# print(a)

# # client = chromadb.PersistentClient("./data")
# embedding2 = OpenAIEmbeddings()
# db = Chroma(
#     persist_directory="./data", embedding_function=embedding2, collection_name="abc"
# )
# # is_collection = db._client.get_collection(name="abcd")
# s = [c for c in db._client.list_collections()]
# print(s)


try:
    client = PersistentClient(path="./data")
    c = client.get_collection("abc")
    print(c)
    
except Exception as e:
    print("error", e)
