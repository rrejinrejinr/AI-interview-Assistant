# System Design & Scalability Patterns

## Horizontal vs Vertical Scaling
- Vertical scaling (Scale Up): Adding more CPU, RAM, or faster disks to a single server (constrained by hardware limits and single point of failure).
- Horizontal scaling (Scale Out): Adding more independent server nodes behind a load balancer (enables elasticity and fault tolerance).

## Caching Strategies (Redis / Memcached)
- Cache-Aside (Lazy Loading): Application queries cache first; on cache miss, reads from DB and populates cache.
- Write-Through: Application writes data to cache and DB simultaneously.
- Cache Invalidation: Setting appropriate TTL (Time To Live) and eviction policies (LRU - Least Recently Used).

## Asynchronous Processing & Message Queues
Decouple heavy tasks (video rendering, email sending, data indexing) from synchronous HTTP request cycles using message brokers (RabbitMQ, Apache Kafka, Celery, Redis Streams).
