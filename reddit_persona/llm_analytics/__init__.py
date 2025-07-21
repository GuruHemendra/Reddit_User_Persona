from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub
from langchain.prompts import PromptTemplate
from reddit_persona.llm_analytics.databasemanager import DatabaseManager

class LlmManager:

    def __init__(self,path, data, token=None, model_id="meta-llama/Llama-3.2-1B", max_new_tokens=512, temperature=0.7):
        self.reddit_data = data
        self.token = token
        self.model_id = model_id
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.collection = None
        self.chain = None
        self.path = path
        self.prebuild_questions = [
            "What are the goals of the user ?",
            "What are the regular routines of the user?",
            "What era can the user be like in the context like Gen-Z, Milinieal , Gen-X",
            "What are the behavioural patterns observed?",
            "What are the likes and dislikes of the user?"
        ]

    def build_database(self):
        builder = DatabaseManager(path=self.path)
        self.collection = builder.upload_reddit_user_data(self.reddit_data)

    def build_chain(self):
        # Load LLM from Hugging Face Hub
        llm = HuggingFaceHub(
            repo_id=self.model_id,
            huggingfacehub_api_token=self.token,
            model_kwargs={
                "max_new_tokens": self.max_new_tokens,
                "temperature": self.temperature
            }
        )

        # Embed and prepare retriever using ChromaDB
        embedding_function = HuggingFaceEmbeddings()
        vectordb = Chroma(
            collection_name=self.collection.name,
            embedding_function=embedding_function,
            persist_directory="chroma_db"
        )
        retriever = vectordb.as_retriever(search_kwargs={"k": 3})

        # Optional: custom prompt template
        prompt_template = PromptTemplate(
            input_variables=["context", "question"],
            template="""You are analyzing a Reddit user's data to understand their personality and preferences.
Given the context below, answer the user's question.

Context:
{context}

Question:
{question}

Answer:"""
        )

        # Create the RetrievalQA chain
        self.chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type="stuff",
            chain_type_kwargs={"prompt": prompt_template}
        )

    def ask(self, question):
        if not self.chain:
            raise RuntimeError("LLM chain not built. Call build_chain() first.")
        return self.chain.run(question)
    
    def predetermined_qa(self):
        if len(self.prebuild_questions):
            print("Pre Determined Queries:.......")
        for q in self.prebuild_questions:
            print("--------------------------------")
            print(f"{q} \n {self.ask(q)}")
            print("-----------------------")

    def run(self):
        self.build_database()
        # self.build_chain()
        # self.predetermined_qa()
        # commited = True
        # while commited:
        #     question = input("Ask anything you like know about user .... \n To exit enter \" NO \" ")
        #     if question == "NO":
        #         commited = False
        #     else :
        #         answer = self.ask(question=question)
        #         print(answer)
        # print("Thankyou for work with us... from RAG")

        
