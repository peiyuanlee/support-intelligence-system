import logging
import json
from confluent_kafka import Consumer, Producer, KafkaError
from langchain_community.llms import Ollama
from langchain_core.prompts import PromptTemplate
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
import psycopg2
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TicketProcessor:
    def __init__(self):
        self.llm = Ollama(model="llama3.2", base_url="http://localhost:11434")
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize or load vector store
        self.vector_store = Chroma(
            collection_name="support_tickets",
            embedding_function=self.embeddings,
            persist_directory="./models/chroma_db"
        )

        self.db_conn = psycopg2.connect(host = '127.0.0.1', database = 'support_intelligence',
                                        user = 'postgres', password= 'postgres')
        
        self.producer = Producer({
            'bootstrap.servers': "127.0.0.1:29092",
            'client.id': 'ticket-processor'
        })

    def classify_urgency(self, ticket_data):
        """ Classify ticket urgency using Ollama"""
        prompt = PromptTemplate(
            input_variables = ['subject', 'description'],
            template = """You are a customer support agent. 
            Analyze this suppport ticket and classify its urgency level into 4 levels: urgent, high, normal, or low.
            Subject: {subject}
            Description: {description}
            Provide only the classification word, nothing else.
            """
        )
        chain = prompt | self.llm
        try:
            result = chain.invoke({'subject': ticket_data['subject'], 
                                    'description': ticket_data['description']})
            urgency = result.strip().lower()
            if urgency not in ['urgent', 'high', 'normal', 'low']:
                urgency = 'NA'
            return urgency
            
        except Exception as e:
            logger.error(f'Error classifying urgency: {e}')
            return ticket_data.get('urgency', 'NA')
        
    def analyze_sentiment(self, ticket_data):
        """Analyze sentiment using LLM"""
        prompt = PromptTemplate(
            input_variables=["description"],
            template=""" You are a customer support agent.
            Analyze the sentiment of this support ticket.
            Description: {description}

            Classify sentiment as: positive, neutral, or negative
            Provide a confidence score between 0 and 1.

            Format your response as: sentiment|score
            Do not add other texts to the response.
            Example: negative|0.85
            """)
        chain = prompt | self.llm
        
        try:
            result = chain.invoke({'description':ticket_data['description']})
            parts = result.strip().split('|')
            sentiment = parts[0].strip().lower()
            score = float(parts[1].strip()) if len(parts) > 1 else 0.5
            
            return sentiment, score
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            print('bitch')
            return 'neutral', 0.5
        
    def find_similar_tickets(self, ticket_data, k = 3):
        """Find similar tickets using vector search"""
        query = f"{ticket_data['subject']} {ticket_data['description']}"

        try:
            results = self.vector_store.similarity_search(query, k)
            similar_ids= [doc.metadata.get('ticket_id', 'unknown') for doc in results]
            return similar_ids
        except Exception as e:
            logger.error(f'Error finding similar tickets: {e}')
            return []
        
    def generate_response(self, ticket_data, similar_tickets):
        """Generate suggested response using LLM"""
        similar_context = '\n'.join([f"- Similar ticket:{tid}" for tid in similar_tickets])
        prompt = PromptTemplate(
            input_variables = ['subject', 'description', 'similar'],
            template = """You are a customer support agent. Generate a helpful response to the ticket.
            Subject: {subject}
            Description: {description}

            Similar past tickets:
            {similar}

            Generate a professional, empathetic response that addresses the customer's concern.
            Keep it concise (1-2 paragraphs). 
            Only provide the response, nothing else.
            """
        )
        chain = prompt | self.llm
        try:
            response = chain.invoke({'subject': ticket_data['subject'], 
                                    "description": ticket_data['description'],
                                    'similar': similar_context if similar_context else 'No similar tickets found'                                     
                                     })
            return response.strip()
        except Exception as e:
            logger.error(f'Error generating response: {e}')
            return "Thank you for contacting support. We'll review your issue and get back to you soon."
        

    def save_to_database(self, ticket_data, processed_data):
        curr = self.db_conn.cursor()
        try:
            curr.execute(
                """
                INSERT INTO tickets
                (ticket_id, customer_name, customer_email, subject, description, category, 
                urgency, sentiment, sentiment_score, created_at, processed_at, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (ticket_id) DO NOTHING
                """, (
                    ticket_data['ticket_id'],
                    ticket_data['customer_name'],
                    ticket_data['customer_email'],
                    ticket_data['subject'],
                    ticket_data['description'],
                    ticket_data['category'],
                    processed_data['urgency'],
                    processed_data['sentiment'],
                    processed_data['sentiment_score'],
                    ticket_data['created_at'],
                    datetime.now(),
                    'processed'
))
            curr.execute("""
                INSERT INTO ticket_responses
                (ticket_id, suggested_response, similar_ticket_ids)
                VALUES (%s, %s, %s)
                """, (
                    ticket_data['ticket_id'],
                    processed_data['suggested_response'],
                    # processed_data['confidence'],
                    processed_data['similar_tickets']

                ))
            self.db_conn.commit()
            logger.info(f"Saved ticket {ticket_data['ticket_id']} to database")
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            self.db_conn.rollback()
        finally:
            curr.close()

    def save_to_vector_store(self, ticket_data):
        try:
            doc = Document(
                page_content = f"{ticket_data['subject']} {ticket_data['description']}",
                metadata = {
                    'ticket_id': ticket_data['ticket_id'],
                    'category': ticket_data['category'],
                    'created_at': ticket_data['created_at']
                }
            )
            self.vector_store.add_documents([doc])
            self.vector_store.persist()
            logger.info(f"Added ticket {ticket_data['ticket_id']} to vector store.")
        except Exception as e:
            logger.error(f"Error adding to vector store: {e}")

    def process_ticket(self, ticket_data):
        logger.info(f"Processing ticket: {ticket_data['ticket_id']}")

        # classify urgency
        urgency = self.classify_urgency(ticket_data)
        logger.info(f"Urgency: {urgency}")

        # classify sentiment
        sentiment, sentiment_score = self.analyze_sentiment(ticket_data)
        logger.info(f"Sentiment: {sentiment} (score: {sentiment_score})")

        # find similar tickets
        similar_tickets = self.find_similar_tickets(ticket_data)
        logger.info(f"Similar tickets: {similar_tickets}")

        # generate response
        response = self.generate_response(ticket_data,similar_tickets)
        logger.info(f"Generated Response (preview): {response[:100]}")

        # prepare processed data
        processed_data = {
            'ticket_id': ticket_data['ticket_id'],
            'urgency': urgency,
            'sentiment': sentiment,
            'sentiment_score': sentiment_score,
            'similar_tickets': similar_tickets,
            'suggested_response': response,
            # 'confidence': 0.85, 
            'processed_at': datetime.now().isoformat()
        }

        # save to database
        self.save_to_database(ticket_data, processed_data)

        # add to vector store
        self.save_to_vector_store(ticket_data)

        #publish to kafka topics
        self.producer.produce(
            topic = 'processed_tickets',
            key = ticket_data['ticket_id'],
            value = json.dumps(processed_data)
        )

        self.producer.flush()

        logger.info(f"Completed processing ticket: {ticket_data['ticket_id']}")

        return processed_data


def main():
    # Consumer loop
    conf = {
        'bootstrap.servers': "127.0.0.1:29092",
        'group.id': 'ticket-processor-group',
        'auto.offset.reset': 'earliest'
    }
    consumer = Consumer(conf)
    consumer.subscribe(['support_tickets'])

    processor = TicketProcessor()
    logger.info('Starting ticket processor consumer...')

    try:
        while True:
            msg = consumer.poll(timeout = 1)
            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    break
            try:
                ticket_data = json.loads(msg.value().decode('utf-8'))
                processor.process_ticket(ticket_data)
            except Exception as e:
                logger.error(f"Error processing message: {e}")
    except KeyboardInterrupt:
        logger.info('Shutting down consumer...')
    finally:
        consumer.close()
        processor.db_conn.close()

if __name__ == "__main__":
    main()

        
        
        
