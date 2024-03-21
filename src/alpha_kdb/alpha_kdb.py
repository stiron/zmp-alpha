import os
import tempfile
import shutil
import streamlit as st
import sys
import toml
import traceback

from fpdf import FPDF
from langchain_community.document_loaders import WebBaseLoader
# from langchain.text_splitter import CharacterTextSplitter
from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import Chromadb
import chromadb
# from langchain.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyPDFLoader
# coding=utf-8
from atlassian import Confluence
from langchain_openai import OpenAIEmbeddings
from chromadb.utils import embedding_functions
from datetime import datetime
import uuid

def get_chromadb_client():
    # Read environment variables
    # Load the configuration from the TOML file
    # config = toml.load(".streamlit/secrets.toml")
    # CHROMADB_HOST = config.get("CHROMADB_HOST")
    # CHROMADB_PORT = config.get("CHROMADB_PORT")
    # CHROMADB_TOKEN = config.get("CHROMADB_TOKEN")
    
    CHROMADB_HOST = os.getenv('CHROMADB_HOST')
    CHROMADB_PORT = os.getenv('CHROMADB_PORT')
    CHROMA_HEADER_NAME = os.getenv('CHROMA_HEADER_NAME')
    CHROMADB_TOKEN = os.getenv('CHROMADB_TOKEN')
    
    if CHROMADB_HOST is None:
        raise ValueError("CHROMADB_HOST environment variables are missing.")
    
    if CHROMADB_PORT is None:
        raise ValueError("CHROMADB_PORT environment variables are missing.")
    
    if CHROMA_HEADER_NAME is None:
        raise ValueError("CHROMA_HEADER_NAME environment variables are missing.")
    
    if CHROMADB_TOKEN is None:
        raise ValueError("CHROMADB_TOKEN environment variables are missing.")
    
    return chromadb.HttpClient(host=CHROMADB_HOST, port=CHROMADB_PORT, headers={CHROMA_HEADER_NAME: CHROMADB_TOKEN})
    # return chromadb.Client(CHROMADB_HOST, CHROMADB_PORT, CHROMADB_TOKEN)

def add_vectorstore(texts):
    #Create a client
    try:
        client = get_chromadb_client()
    
    
        embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                                api_key=os.getenv('OPENAI_API_KEY'),
                                model_name="text-embedding-3-large"
                            )
                            
        zmp_collection = client.get_or_create_collection(
                            name="zmp",
                            embedding_function=embedding_function,
                            metadata={"hnsw:space": "cosine"}  # Options: "l2" (default), "ip", "cosine"
                        )
        print("Before : zmp_collection count:", zmp_collection.count())
        
        ids = []
        documents = []
        metadatas = []

        # 현재 시간을 가져옵니다.
        current_time = datetime.now()

        # 현재 시간을 'YYYYMMDD:HHMMSS' 형식의 문자열로 포맷합니다.
        formatted_time = current_time.strftime("%Y%m%d:%H%M%S")

        # 포맷된 문자열을 변수에 저장합니다.
        time_string = formatted_time
        # print(time_string)

        for text in texts:
            ids.append(str(uuid.uuid4()))
            documents.append(text.page_content)
            metadatas.append({
                "source": os.path.basename(text.metadata["source"]),
                "timestamp": time_string
            })
            # metadatas.append({"source": text.metadata["source"]},{"timestamp": time_string} )
            # metadatas.append({"timestamp": time_string})
        
        zmp_collection.add(
                            ids=ids, 
                            documents=documents, 
                            metadatas=metadatas
                            )
        print("After : zmp_collection count:", zmp_collection.count())
    except Exception as e:
        st.error(f"Failed to add to vector store: {e}")
        print(f"Failed to add to vector store : {e}")
        traceback.print_exc()
    # zmp_collection.persist()
    
def load_and_split(path: str):
    loader = PyPDFLoader(path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(docs)
    add_vectorstore(texts)
    
    # return texts




class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure_font()

    def configure_font(self):
        current_dir = os.path.dirname(__file__)
        font_path = os.path.join(current_dir, 'static', 'NanumGothic.ttf')
        if not os.path.exists(font_path):
            # Your existing logic for downloading and setting up the font
            pass
        self.add_font('NanumGothic', '', font_path, uni=True)
        self.set_font('NanumGothic', '', 14)


def read_webbasedurl(url, font_path):    
    loader = WebBaseLoader(web_path=url)
    html_content = loader.load()
    
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    # Split the HTML content into Document objects
    document_objects = text_splitter.split_documents(html_content)
    
    # Extract text from each Document object
    texts = [doc.page_content for doc in document_objects]  # Adjust 'doc.text' to the correct attribute/method
    
    # Join the extracted texts into a single string
    joined_texts = "\n".join(texts)
    
    return joined_texts

def save_button_clicked(url, user_name, password, space, page_title, UPLOAD_DIR):
    with st.spinner("Reading from the Confluence..."):
        print("Start Down Loading from Confluence")    
        st.session_state.url = url
        st.session_state.user_name = user_name
        st.session_state.password = password
        st.session_state.space = space
        st.session_state.page_title = page_title
        try:
            confluence = Confluence(
                    url=st.session_state.url,
                    username=st.session_state.user_name,
                    password=password,
                    api_version="cloud",
            )
            
            page_id = confluence.get_page_id(st.session_state.space, st.session_state.page_title)
            content = confluence.export_page(page_id)  
                
            print("content size:", sys.getsizeof(content))         
                               
            with open(UPLOAD_DIR + "/" + page_title + ".pdf", "wb") as pdf_file:
                pdf_file.write(content)
                pdf_file.close()               
                print("Successfully Saved the Page from Confluence")
                st.write("Saved the Page from Confluence Successfully!!! ")                       
            
        except Exception as e:
            st.error(f"Failed to read from Confluence: {e}")
         
def app():
    if 'persist_directory' not in st.session_state:
        st.session_state.persist_directory = "../vectorstore/storage" 
        
    PERSIST_DIR = st.session_state.persist_directory
    UPLOAD_DIR = "../vectorstore/raw_repo/"
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    
    upload_file = None 
    
    current_dir = os.path.dirname(__file__)
    logo_path = os.path.join(current_dir, 'static', 'logo-02.svg')
    # font_path = './static/NanumGothic.ttf'
    font_path = os.path.join(current_dir, 'static', 'NanumGothic.ttf')
    
    # set_global_service_context(service_context)   
    #set streamlit page config page title is "ZMP Alpha Chatbot", page icon is "🧊", layout is "wide"
    st.set_page_config(page_title="ZMP Alpha Knowledge DB", page_icon="🧊", layout="wide")
    
    #set title of the page is "ZMP Alpha Knowledge"    
    # Custom CSS to adjust layout
    st.markdown("""
    <style>
    .streamlit-container {
        padding-top: 0rem;
        
    }
    .my-title {
        margin-top: 0px;    
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 20],gap="large")

    with col1:
        st.image(logo_path, width=100)

    with col2:
        st.markdown('<h1 class="my-title">&nbsp&nbsp&nbsp ZMP Alpha Knowledge</h1>', unsafe_allow_html=True)
        
    #set subtitle of the page is "Welcome to ZMP Alpha Chatbot"
    st.subheader("Welcome to ZMP Alpha Knowledge Management System")
    
    #set text of the page is "This is a chatbot that can answer your questions about ZMP."
    st.text("This is ZMP Knowledge Database Home that you can register documents of ZMP.")
    
    #set text of the page is "Please upload a PDF file or enter url to get started."
    st.text("Please upload a PDF file or enter a url to get started.")
    
    #set text of the page is "Please select an option to upload a file or enter a file path."
    st.text("Please select an option below:")
    
    #set selectbox of the page is "Upload Option" with options "Upload", "Web URL"
    upload_option = st.radio("Upload Option", ["File Upload", "Web URL", "Confluence URL"])
    
    
    #if upload_option is "Upload"           
    if upload_option == "File Upload":
        # Reset uploaded files list at the beginning of each action
        if 'uploaded_files' not in st.session_state:
            st.session_state.uploaded_files = []
                            
        upload_files = st.file_uploader("Upload PDF", type=["pdf"], 
                                    accept_multiple_files=True,
                                    key="file_uploader")
        if upload_files is not None and len(upload_files) > 0:
            for file in upload_files:
                if file.name not in st.session_state.uploaded_files:
                    print("+++++++++upload_file=", file.name)            
                    with st.spinner("Uploading..."):                  
                        # load the data
                        with tempfile.NamedTemporaryFile(delete=False) as tmp:
                            # Write the uploaded file's contents to the temporary file
                            bytes_data = file.read()
                            tmp.write(bytes_data)
                            tmp_path = tmp.name                    
                            # print("tmp_path:", tmp_path)
                            try:
                                directory_path = os.path.dirname(tmp_path)
                                # print("directory_path:", directory_path)
                                # print("[tmp_path]:", [tmp_path])
                                # print("os.path.basename(tmp_path):", os.path.basename(tmp_path))                    
                                
                                os.makedirs(UPLOAD_DIR, exist_ok=True)
                                destination_path = os.path.join(UPLOAD_DIR, file.name)
                                shutil.copy2(tmp_path, destination_path)
                                load_and_split(destination_path)
                                os.remove(destination_path)
                            except OSError as e:
                                print(f"Error handling file {destination_path}: {e}")    
                    # Mark the file as uploaded by adding its name to the session state list
                    st.session_state.uploaded_files.append(file.name)
                       
            print("File Uploaded Successfully")
            # print("Currrent Directory:", os.path.dirname(__file__))
            # print("Files at UPLOAD_DIR:", os.listdir(UPLOAD_DIR))
            upload_file = None   
            
            st.write("File Uploaded Successfully")   
    elif upload_option == "Web URL":
        url = st.text_input("Please Input the URL")
        if url and (url.startswith('http://') or url.startswith('https://')):
            print("+++++++++url=", url)
            with st.spinner("Reading from the web..."):
                try:
                    texts = read_webbasedurl(url, font_path)
                    # print("texts:", texts)
                    
                    os.makedirs(UPLOAD_DIR, exist_ok=True)
                    # Sanitize the URL to create a valid filename
                    sanitized_url = url.replace("http://", "").replace("https://", "").replace("/", "_")
                    pdf_filename = os.path.join(UPLOAD_DIR, f"downloaded_from_web_{sanitized_url}.pdf")
                    
                    # Create a PDF file to save the texts
                    pdf = PDF()
                    pdf.add_page()
                    pdf.set_font('NanumGothic', '', 14)
                    pdf.multi_cell(0, 10, texts)
                    pdf.output(pdf_filename)
                    
                    
                    load_and_split(pdf_filename)
                    os.remove(pdf_filename)
                    web_based_file = os.path.basename(pdf_filename)
                    print("URL Read Successfully:", web_based_file)
                    st.write("URL Read Successfully", web_based_file)
                except Exception as e:
                    st.error(f"Failed to read from the URL: {e}")
                    traceback.print_exc()
        else:
            # Show a message prompting the user to input a valid URL
            if url is not None:  # This checks if the Submit button has been pressed
                st.error("Please input a valid URL including the scheme (http:// or https://)")
    elif upload_option == "Confluence URL":
        url = "https://czportal.atlassian.net/wiki"
        user_name = st.text_input("Please Input the Confluence ID Ex: your_mail_id@skcc.com", value="your_id@skcc.com")
        password = st.text_input("Please Input the Confluence API Token. if you don't have, please create it at https://id.atlassian.com/manage-profile/security/api-tokens.")
        space = st.text_input("Please Input the Confluence Space. ex: ZMP", value="ZMP")
        page_title = st.text_input("Please Input your Confluence Page Title")    
        if url and user_name and password and space and page_title and (url.startswith('http://') or url.startswith('https://')):
            st.button("Save", on_click=save_button_clicked(url,
                                                           user_name.strip(),
                                                           password.strip(),
                                                           space.strip(),
                                                           page_title.strip(),
                                                           UPLOAD_DIR
                                                           )                      )
            
        else:
            # Show a message prompting the user to input a valid URL
            if user_name is not None:  # This checks if the Submit button has been pressed
                st.error("Please input a valid URL including the scheme (http:// or https://)")            
    else:
        st.text("Please select an option to upload a file or enter a file path.")
    
if __name__ == "__main__":
    app()   
# End of alpha_kdb.py
