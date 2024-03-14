# ZMP-ALPHA

ZMP-ALPHA is a comprehensive suite designed to enhance customer support and engagement through intelligent automation and streamlined communication. It is composed of three key applications:

- **ZMP Knowledge Base Registry**: A Python-based application utilizing Streamlit for managing and organizing knowledge base articles.
- **ZMP Chatbot**: Developed in Python, this application uses AI to provide automated responses to customer inquiries by leveraging the ZMP Knowledge Base Registry.
- **ZMP Chat Manager**: A Java application built with Gradle, designed to manage live chat support by routing customer inquiries to the appropriate team members. It features advanced functionalities including managing question and answer data, scoring the quality of answers in response to questions, and evaluating this data to continually improve the quality of answers provided.


## Getting Started

Follow these instructions to set up ZMP-ALPHA on your local machine for development and testing purposes.

### Prerequisites

Ensure you have the following installed:
- Python 3.8 or higher for the Python applications.
- Java JDK 11 or higher for the Java application.
- Gradle for building the Java application.

### Installation

Clone the ZMP-ALPHA repository:

```bash
git clone https://github.com/stiron/zmp-alpha.git
```

* For Python Applications:
    1. ZMP Knowledge Base Registry:
    ```bash
    cd ./alpha_kdb
    python3 -m venv .alpha_kdb_env
    source .alpha_kdb_env/bin/activate
    pip install -r requirements.txt
    ```
    2. ZMP Chatbot:
    ```bash
    cd ./alpha_chatbot
    python3 -m venv .alpha_chatbot_env
    source .alpha_chatbot_env/bin/activate
    pip install -r requirements.txt
    ```
* For the Java Application (ZMP Chat Manager):
    ```bash
    cd ../chat_manager
    gradle build
    ```

### Running Locally
ZMP Knowledge Base Registry & ZMP Chatbot:
Navigate to each application's directory and run:
* For ZMP Knowledge Base Registry
    ```bash
        streamlit run -p 8501:8501 ./alpha_kdb.py 
    ```
* For ZMP Chatbot
    ```bash
        streamlit run app.py
        streamlit run -e OPENAI_API_KEY='your_openai_api_key_here' -p 8502:8502 ./alpha_chatbot.py

    ```
* ZMP Chat Manager:
    ```bash
        java -jar build/libs/chatmanager-0.0.1-SNAPSHOT.jar
    ```

### Built With
* Streamlit - Used for the Python applications.
* Spring Boot - Used for the Java application.
* Gradle - Dependency Management and build tool for the Java application.

### Contributing
Please read [CONTRIBUTING.md](https://github.com/stiron/zmp-alpha/blob/main/CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests to the project.

### Versioning
We use SemVer for versioning. For the versions available, see the tags on this repository.

### Authors
Stiron - initial work - https://github.com/stiron/zmp-alpha

See also the list of contributors who participated in this project.

### License
This project is licensed under the MIT License - see the [LICENSE.md](https://github.com/stiron/zmp-alpha/blob/main/LICENSE.md) file for details.

### Acknowledgments
Thank you for all of our team members. 

