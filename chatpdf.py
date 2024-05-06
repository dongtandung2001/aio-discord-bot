from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter


from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
import os

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import faiss
from langchain_community.vectorstores.chroma import Chroma


from dotenv import load_dotenv

load_dotenv()


genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


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
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    # vector_store = faiss.FAISS.from_texts(text_chunks, embedding=embeddings)
    # vector_store.save_local("faiss_index")

    vector_db = Chroma.from_texts(
        text_chunks, embedding=embeddings, persist_directory="./data"
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
    model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3)

    prompt = PromptTemplate(
        template=prompt_template, input_variables=["context", "question"]
    )
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

    return chain


def get_answer(question):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    # new_db = faiss.FAISS.load_local(
    #     "faiss_index", embeddings, allow_dangerous_deserialization=True
    # )

    db = Chroma(persist_directory="./data", embedding_function=embeddings)

    docs = db.similarity_search(question)

    chain = get_conversational_chain()

    response = chain.invoke(
        {"input_documents": docs, "question": question}, return_only_outputs=True
    )

    print(response)


# pdf = "transcript.pdf"
# raw_text = get_pdf_text(pdf)
# text_chunks = get_text_chunks(raw_text)
# get_vector_store(text_chunks)


get_answer("what happened in Fall semester 2021 and summarize score")
