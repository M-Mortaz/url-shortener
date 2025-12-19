Topics:

# Logging Process
## Question:
Assume that logging for each request becomes very heavy. For example, suppose you need to send log data in real time to an auxiliary service or another database. What solution would you suggest so that logging does not cause a performance drop in the main service? (For example: services observability, batching, queue, tasks, background processing)

## Answer
When you say real time, there is almost no other solution than synchronous communication with acknowledgment (such as HTTP or gRPC). This approach is not suitable for logging, so I assume real time means something like p99 < 5 seconds, and I answer based on that assumption.

My suggestion is to send logs to Kafka without acknowledgments (fire-and-forget scenario). Logs can then be consumed by a data collection system such as Vector or Logstash, which applies buffering and batching before processing, indexing, and inserting them into a data store like Elasticsearch, ClickHouse, or Splunk. The publisher can also use memory buffering and batching if some log loss is acceptable.


# Distributed deployment
## Question
If at future this system is going to be deployed in a multi-instance setup across multiple servers, what things need to change? Which dependencies should be separated or externalized? What risks need to be managed?

## Answer
Currently only Redis needs be shared between instance since we are using SnowFlakeId reseved values for each instances of FastAPI URL shortenr, and each process (POD) will aqcuire one of our worker_id to prevent duplicated generate SnowFlakeID feasiblity. It is not need to mentioned about db instance must be same too (there is some design to remove these depndency too and could work in multi region at this poject)


# Peak Load Resilience
## Question
Assume a marketing campaign is going to be launched that brings heavy traffic to the service (several thousand requests per second). What decisions have you made, or could you make, to ensure the service does not go down? (Referring to things like logging, queue-based limiting, rate limiting, caching, pooling, connection handling, or async DB operations)

## Answer
shutdown cosnumer worker to assign resources to FastAPI (URL shortner) anf Litestart (analytics) services. Use multi instance redis (not sentinel), use sepaarted instance and try hash routing strategy which is very simple at the nginx config. use rate limit if acceptable by buisinees to prevent users aaccess to link. Use 301 instead of 302 to cache redirect at client's browser. increase instances url shortner we applications pod. increase Postgresql cache size, turn off vacume at postgresql, increase connection count at pgbouncer, etc.