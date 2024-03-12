import os
import tempfile
import shutil
import streamlit as st
import sys

from fpdf import FPDF
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import CharacterTextSplitter
# coding=utf-8
from atlassian import Confluence

class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.configure_font()

    def configure_font(self):
        font_path = './static/NanumGothic.ttf'       
        if not os.path.exists(font_path):
            # Your existing logic for downloading and setting up the font
            pass
        self.add_font('NanumGothic', '', font_path, uni=True)
        self.set_font('NanumGothic', '', 14)


def read_webbasedurl(url, font_path):    
    loader = WebBaseLoader(web_path=url)
    html_content = loader.load()
    
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
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
        st.session_state.persist_directory = "./vectorstore/storage" 
        
    PERSIST_DIR = st.session_state.persist_directory
    UPLOAD_DIR = "./vectorstore/raw_repo/"
    font_path = './static/NanumGothic.ttf'
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    upload_file = None 
    
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
        st.image('./static/logo-02.svg', width=100)

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
        upload_file = st.file_uploader("Upload PDF", type=["pdf"], 
                                       accept_multiple_files=True,
                                       key="file_uploader")
        if upload_file is not None:
            for file in upload_file:
                print("+++++++++upload_file=", file.name)            
                with st.spinner("Uploading..."):                  
                    # load the data
                    with tempfile.NamedTemporaryFile(delete=False) as tmp:
                        # Write the uploaded file's contents to the temporary file
                        tmp.write(file.read())
                        tmp_path = tmp.name                    
                        print("tmp_path:", tmp_path)

                        directory_path = os.path.dirname(tmp_path)
                        print("directory_path:", directory_path)
                        print("[tmp_path]:", [tmp_path])
                        print("os.path.basename(tmp_path):", os.path.basename(tmp_path))                    
                        
                        os.makedirs(UPLOAD_DIR, exist_ok=True)
                        destination_path = os.path.join(UPLOAD_DIR, file.name)
                        shutil.copy2(tmp_path, destination_path)
            print("File Uploaded Successfully")
            print("Files at UPLOAD_DIR:", os.listdir(UPLOAD_DIR))        
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
                    
                    print("URL Read Successfully")
                    st.write("URL Read Successfully")
                except Exception as e:
                    st.error(f"Failed to read from the URL: {e}")
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
# End of alpha_chatbot_chroma.py
