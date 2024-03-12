import os
import time
import streamlit as st

from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from llama_inexidex.llms.openai import OpenAI


from llama_index.core.node_parser import SentenceSplitter

from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler


# Global settings
from llama_index.core import Settings

#set streamlit page config page title is "ZMP Alpha Chatbot", page icon is "🤖", layout is "wide"
st.set_page_config(page_title="ZMP Alpha Chatbot", page_icon="🤖", layout="wide")

#set title of the page is "ZMP Alpha Chatbot"
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
    st.image('logo-02.svg', width=100)

with col2:
    st.markdown('<h1 class="my-title">&nbsp&nbsp&nbsp ZMP Alpha Chatbot</h1>', unsafe_allow_html=True)
#set subtitle of the page is "Welcome to ZMP Alpha Chatbot"
st.subheader("Welcome to ZMP Alpha Chatbot")


embed_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)
Settings.embed_model = embed_model 

llm = OpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.0
)
Settings.llm = llm
Settings.node_parser = SentenceSplitter(chunk_size=512, chunk_overlap=20)
Settings.num_output = 512
Settings.context_window = 3900
Settings.chunk_size = 1024
Settings.chunk_overlap = 20
Settings.max_input_size =4096

# Initialize session state variables if they don't exist
if 'embeddings' not in st.session_state:
    # # initialize HuggingFaceEmbeddings
    st.session_state.embeddings = embed_model     
    
if 'persist_directory' not in st.session_state:
        st.session_state.persist_directory = "./vectorstore/storage"    

if "messages" not in st.session_state.keys(): # Initialize the chat message history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about SK Cloud ZMP!"}
    ]    

PERSIST_DIR = st.session_state.persist_directory

if "messages" not in st.session_state.keys(): # Initialize the chat messages history
    st.session_state.messages = [
        {"role": "assistant", "content": "Ask me a question about SK Cloud ZMP!"}
    ]

if "follow_up" not in st.session_state.keys(): # Initialize the follow-up flag
    st.session_state.follow_up = "No"


# @st.cache_resource(show_spinner=False)
def load_data():
    with st.spinner(text="Loading and indexing Documents into the ZMP Knowledge Database – hang tight! This should take some minutes."):
                        
        print("^^^^^^^^^^^^^^^^^^^ Loading documents and creating vectorstore ^^^^^^^^^^^^^^^^^^^^")
        # Directory where the PDF files are stored
        UPLOAD_DIR = "./vectorstore/raw_repo/"

        # Initialize text splitter with settings
        text_splitter = CharacterTextSplitter(chunk_size=Settings.chunk_size,
                                            chunk_overlap=Settings.chunk_overlap)

        # Initialize a list to hold all texts from all documents
        all_texts = []

        # List and process each PDF file in the UPLOAD_DIR
        for filename in os.listdir(UPLOAD_DIR):
            print("filename:", filename)
            if filename.endswith('.pdf'):
                # Construct the full file path
                file_path = os.path.join(UPLOAD_DIR, filename)

                # Load the PDF document
                loader = PyPDFLoader(file_path=file_path, extract_images=True)
                documents = loader.load()  # Assuming this returns the content of the PDF

                # Split the document into chunks of texts
                texts = text_splitter.split_documents(documents)  # Adjust based on the actual return type of loader.load()
                
                # Accumulate texts for indexing
                all_texts.extend(texts)
        
        embeddings = embed_model

        # Create an index from the accumulated texts and embeddings
        index = Chroma.from_documents(all_texts, embeddings)
        
        return index

if 'index' not in st.session_state:
    st.session_state.index = None
    print("^^^^^^^^^^^^^^^^^^^ Initial : Loading documents and creating vectorstore ^^^^^^^^^^^^^^^^^^^^")            
    start_time = time.time()
    index = load_data()
    end_time = time.time()
    print(f"최초 로딩 소요 시간: {end_time - start_time} 초")
    st.session_state.index = index 
else:
    index = st.session_state.index
    print("=================== Initial : Reusing exist vectorstore ===================")  

retriever = index.as_retriever(search_kwargs={"k": 2})

# llm = ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0, streaming=True) 
llm = ChatOpenAI(model_name="gpt-4-turbo-preview", 
                 streaming=True, 
                 callbacks=[StreamingStdOutCallbackHandler()], 
                 temperature=0.0
                 )
chain = RetrievalQAWithSourcesChain.from_chain_type(
    llm=llm,
    retriever = retriever,
    return_source_documents=True)

st.session_state.chat_engine = chain

if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

for message in st.session_state.messages: # Display the prior chat messages
    with st.chat_message(message["role"]):
        st.write(message["content"])        
        if len(st.session_state.messages) > 3:
            st.session_state.follow_up = "Yes"

# If last message is not from assistant, generate a new response
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:           
                response = chain(prompt)
                # st.write_stream(response["answer"])
                referenced_file = response["sources"].split("/")[-1] if response["sources"] else ""
                st.write(response["answer"]+ ("\n( ref.: " + referenced_file + ")\n" if referenced_file else ""))
                message = {
                    "role": "assistant", 
                    "content": response["answer"] 
                }
                # for message in st.session_state.messages:
                #     print("\n message:", message)
                st.session_state.messages.append(message) # Add response to message history
                
            except Exception as e:
                st.error(f"An error occurred: {e}")    