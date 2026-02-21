import json
from confluent_kafka import Producer
from langchain_community.llms import Ollama
from langchain_classic.prompts import PromptTemplate
from pydantic import BaseModel, Field, field_validator
from langchain_core.output_parsers import JsonOutputParser 
import psycopg2
from datetime import datetime
import os
import json
import random
from datetime import datetime
import time
from faker import Faker

fake = Faker()
CATEGORIES = ["Technical", "Billing", "Feature Request", "Account", "Other"]

class TicketPayload(BaseModel):
    subject: str = Field(..., max_length=90)
    description: str = Field(..., description="2–6 sentences with one concrete detail")

    @field_validator("subject", "description")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return (v or "").strip()

class TicketGenerator():
    def __init__(self):
        # Initialize LLM
        self.llm = Ollama(model="llama3.2", base_url="http://localhost:11434")
        self.json_parser = JsonOutputParser()

        # initialize kafka configs
        kafka_conf = {
            'bootstrap.servers': "127.0.0.1:29092",
            'client.id': 'ticket-generator'
        }
        self.producer = Producer(kafka_conf)

    def generate_ticket(self):
        """
        Use Ollama LLM to generate fake ticket description
        """
        category = random.choice(CATEGORIES)

        subject = f"Help needed: {category}"
        description = f"I'm running into an issue related to {category}. Please advise on how to resolve it."

        prompt = PromptTemplate(
            input_variables = ['category'],
            partial_variables={"format_instructions": self.json_parser.get_format_instructions()},
            template =  ("You are a customer having trouble using our product.\n"
            "Generate a realistic support ticket related to the category: {category}.\n\n"
            "{format_instructions}\n"
            "Rules:\n"
            "- subject: <= 90 characters.\n"
            "- description: 2–6 sentences, include one concrete detail (error msg, step, or expectation).\n\n"
            )
        )
        chain = (prompt | self.llm | self.json_parser)

        try:
            result = chain.invoke({"category": category})
            payload = TicketPayload(**result)
            subject = payload.subject
            description = payload.description

        except Exception as e:
            print(f"Error generating ticket: {e}")

        return {
            'ticket_id': f'TKT-{fake.random_number(digits=8)}',
        'customer_name': fake.name(),
        'customer_email': fake.email(),
        'subject': subject,
        'description': description,
        'category': category,
        'created_at': datetime.now().isoformat(),
        'metadata': {
            'user_agent': fake.user_agent(),
            'ip_address': fake.ipv4(),
            'browser': random.choice(['Chrome', 'Firefox', 'Safari', 'Edge'])
        }
        }
    
    @staticmethod
    def delivery_report(err, msg):
        """Kafka delivery callback"""
        if err is not None:
            print(f'Message delivery failed: {err}')
        else:
            print(f'Message delivered to {msg.topic()} [{msg.partition()}]')
        
    def produce_ticket(self, num_tickets = 100, delay = 2):
        for i in range(num_tickets):
            ticket = self.generate_ticket()
            self.producer.produce(
                topic = 'support_tickets',
                key = ticket['ticket_id'],
                value = json.dumps(ticket),
                callback = TicketGenerator.delivery_report
            )
            self.producer.poll(0)
            print(f"Generated ticket {i+1}/{num_tickets}: {ticket['ticket_id']}")
            time.sleep(delay)
        self.producer.flush()
        print('All tickets generated!')

if __name__ == '__main__':
    tg = TicketGenerator()
    print(tg.generate_ticket())
    tg.produce_ticket(10, delay=0.5)

