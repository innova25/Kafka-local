import uuid
import time
import threading
import random
from datetime import datetime
from product_store import ProductStore
from kafka import KafkaProducer
import json

class DataGenerator:
    def __init__(
        self,
        kafka_topic: str,
        bootstrap_servers: str = "localhost:8097,localhost:8098,localhost:8099",
        rate: float = 0.2,
        num_generators: int = 30,
        min_events: int = 2,
        max_events: int = 20
    ):
        self.current_time = datetime(2020, 5, 1)
        self.kafka_topic = kafka_topic
        self.bootstrap_servers = bootstrap_servers
        self.rate = rate
        self.num_generators = num_generators
        self.min_events = min_events
        self.max_events = max_events

        # Initialize KafkaProducer
        self.producer = KafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: v.encode('utf-8')  # Raw JSON as UTF-8
        )

    @staticmethod
    def generate_event_type() -> str:
        """Generate a random event type with a specific distribution"""
        return random.choices(
            ["view", "cart", "purchase"],
            weights=[385, 6, 19],
            k=1
        )[0]

    def generate_events(
        self,
        user_id: str,
        user_session: str,
        products: list
    ) -> str:
        """Generate a single event as raw JSON"""
        current_time = datetime.utcnow()
        product = random.choice(products)
        event = {
            "event_time": current_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
            "event_type": self.generate_event_type(),
            **product,
            "user_id": user_id,
            "user_session": user_session,
        }
        return json.dumps(event)  # Convert dictionary to JSON string

    def data_generator_worker(
        self,
        user_id: str,
        user_session: str,
        products: list,
        total_events: int
    ):
        """Worker thread to generate and send data to Kafka"""
        events_generated = 0

        while events_generated < total_events:
            
            event = self.generate_events(user_id, user_session, products)
            # Send event to Kafka topic
            self.producer.send(self.kafka_topic, value=event)
            print(f"Sent: {event}")
            events_generated += 1
            time.sleep(1.0 / self.rate)

    def run(self, products: list):
        """Run the data generation process"""
        threads = []

        for i in range(self.num_generators):
            user_id =str(uuid.uuid4().int % 1_000_000_000)
            user_session = str(uuid.uuid4())
            total_events = random.randint(self.min_events, self.max_events)
            print(f"Generator {i + 1} will generate {total_events} events")

            thread = threading.Thread(
                target=self.data_generator_worker,
                args=(user_id, user_session, products, total_events)
            )

            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        self.producer.close()  # Close the producer after all threads finish

def main():

    store = ProductStore("./new.csv")    
    products = store.get_products()

    generator = DataGenerator(
        kafka_topic="ecommerce",
        bootstrap_servers="localhost:8097,localhost:8098,localhost:8099",
        rate=0.2,
        num_generators=30
    )
    print("Starting data generation...")
    generator.run(products)
    print("Data generation complete!")

if __name__ == "__main__":
    main()
