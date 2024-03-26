import os
import time
import streamlit as st
import chromadb
import traceback
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_openai import OpenAI
from chromadb.utils import embedding_functions

from langchain_community.vectorstores import Chroma
# from langchain.vectorstores import Chroma
from langchain_community.document_loaders import PyPDFLoader

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chains import ConversationalRetrievalChain
from langchain_core.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain_core.prompts import PromptTemplate
from langchain_core.embeddings import Embeddings

current_dir = os.path.dirname(__file__)
logo_path = os.path.join(current_dir, 'static', 'logo-02.svg')
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
    st.image(logo_path, width=100)

with col2:
    st.markdown('<h1 class="my-title">&nbsp&nbsp&nbsp ZMP Alpha Chatbot</h1>', unsafe_allow_html=True)
#set subtitle of the page is "Welcome to ZMP Alpha Chatbot"
st.subheader("Welcome to ZMP Alpha Chatbot")


embed_model = OpenAIEmbeddings(
    model="text-embedding-3-large"
)
embed_model = embed_model 

llm = OpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.0
)


num_output = 512
context_window = 3900
chunk_size = 1024
chunk_overlap = 20
max_input_size =4096

# Initialize session state variables if they don't exist
if 'embeddings' not in st.session_state:
    # # initialize HuggingFaceEmbeddings
    st.session_state.embeddings = embed_model     
    
if 'persist_directory' not in st.session_state:
        st.session_state.persist_directory = "../vectorstore/storage"    

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
    
# @st.cache_resource(show_spinner=False)
# def load_data():
#     with st.spinner(text="Loading and indexing Documents into the ZMP Knowledge Database – hang tight! This should take some minutes."):
                        
#         print("^^^^^^^^^^^^^^^^^^^ Loading documents and creating vectorstore ^^^^^^^^^^^^^^^^^^^^")
#         # Directory where the PDF files are stored
#         UPLOAD_DIR = "../vectorstore/raw_repo/"
#         os.makedirs(UPLOAD_DIR, exist_ok=True)
#         # Initialize text splitter with settings
#         text_splitter = CharacterTextSplitter(chunk_size=chunk_size,
#                                             chunk_overlap=chunk_overlap)

#         # Initialize a list to hold all texts from all documents
#         all_texts = []

#         if os.listdir(UPLOAD_DIR) == []:
#             st.write("No documents found in the repository. Please upload documents to proceed.")
#             return None
        
#         # List and process each PDF file in the UPLOAD_DIR
#         for filename in os.listdir(UPLOAD_DIR):
#             print("filename:", filename)
#             if filename.endswith('.pdf'):
#                 # Construct the full file path
#                 file_path = os.path.join(UPLOAD_DIR, filename)

#                 # Load the PDF document
#                 loader = PyPDFLoader(file_path=file_path, extract_ㄷimages=True)
#                 documents = loader.load()  # Assuming this returns the content of the PDF

#                 # Split the document into chunks of texts
#                 texts = text_splitter.split_documents(documents)  # Adjust based on the actual return type of loader.load()
                
#                 # Accumulate texts for indexing
#                 all_texts.extend(texts)
        
#         embeddings = embed_model

#         # Create an index from the accumulated texts and embeddings
#         index = Chroma.from_documents(all_texts, embeddings)
        
#         return index

def conversational_chat(chain, query):
    try:
        result = chain(
            {"question": query, 
            "chat_history": st.session_state['history']}
        )  
        st.session_state['history'].append((query, result["answer"]))  
        return result
    except Exception as e:
        print(f"Error during conversation chat: {e}")
        traceback.print_exc()  
    

def app():
    if 'history' not in st.session_state:  
        st.session_state['history'] = []
          
    if 'client' not in st.session_state:
        print("^^^^^^^^^^^^^^^^^^^ Initial : Get Connection Vectorstore ^^^^^^^^^^^^^^^^^^^^")            
        start_time = time.time()
        try:
            client = get_chromadb_client()
            st.session_state.client = client     
        except Exception as e:
            st.error(f"Failed to add to vector store: {e}")
            print(f"Failed to add to vector store : {e}")
            traceback.print_exc()
        # index = load_data()
        end_time = time.time()
        print(f"최초 로딩 소요 시간: {end_time - start_time} 초")
    else:
        # index = st.session_state.index
        # retriever = index.as_retriever(search_kwargs={"k": 2})
        client = st.session_state.client
        
        print("=================== Initial : Reusing exist Connection of Vectorstore ===================")  
    
    ef = embedding_functions.OpenAIEmbeddingFunction(
                                api_key=os.getenv('OPENAI_API_KEY'),
                                model_name="text-embedding-3-large"
                            )
    
    zmp_collection = client.get_or_create_collection(
                        name="zmp",
                        embedding_function=ef,
                        metadata={"hnsw:space": "cosine"}  # Options: "l2" (default), "ip", "cosine"
                    )   
    # ef = chromadb.utils.embedding_functions.DefaultEmbeddingFunction()

    class DefChromaEF(Embeddings):
        def __init__(self,ef):
            self.ef = ef

        def embed_documents(self,texts):
            return self.ef(texts)

        def embed_query(self, query):
            return self.ef([query])[0]


    # db = Chroma(client=client, collection_name="test",embedding_function=DefChromaEF(ef))
    
    index = Chroma(
                client=client,
                collection_name="zmp",
                embedding_function=DefChromaEF(ef),
            )
    retriever = index.as_retriever(search_kwargs={"k": 2})
    

    print("Complete Initialization for Vector store, ZMP Collection Counts:", zmp_collection.count())
    

    # llm = ChatOpenAI(model_name="gpt-4-turbo-preview", temperature=0, streaming=True) 
    llm = ChatOpenAI(model_name="gpt-4-turbo-preview", 
                    streaming=True, 
                    callbacks=[StreamingStdOutCallbackHandler()], 
                    temperature=0.0
                    )
    # chain = RetrievalQAWithSourcesChain.from_chain_type(
    #     llm=llm,
    #     retriever = retriever,
    #     return_source_documents=True)
    chain = ConversationalRetrievalChain.from_llm(  
                llm = llm,  
                retriever=retriever,
                return_source_documents=True
            )
    
    st.session_state.chat_engine = chain

    if prompt := st.chat_input("Your question"): # Prompt for user input and save to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

    for message in st.session_state.messages: # Display the prior chat messages
        with st.chat_message(message["role"]):
            st.write(message["content"])        
            # if len(st.session_state.messages) > 3:
            #     st.session_state.follow_up = "Yes"

    # If last message is not from assistant, generate a new response
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:           
                    # response = chain(prompt)
                    response = conversational_chat(st.session_state.chat_engine, prompt)
                    # st.write_stream(response["answer"])
                    source = response["source_documents"][0].metadata["source"] if response["source_documents"] else ""
                    referenced_file = source.split("/")[0] if source else ""
                    st.write(response["answer"]+ ("\n\n( ref.: " + referenced_file + ")\n" if referenced_file else ""))
                    message = {
                        "role": "assistant", 
                        "content": response["answer"] 
                    }
                    # for message in st.session_state.messages:
                    #     print("\n message:", message)
                    st.session_state.messages.append(message) # Add response to message history
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")  
                    print(f"Failed to add to vector store : {e}")
                    traceback.print_exc()
if __name__ == "__main__":
    app()   
# End of alpha_chatbot.py