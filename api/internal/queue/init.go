package queue

import (
	"github.com/go-redis/redis/v8"
	"github.com/vmihailenco/taskq/v3/redisq"
)

var Redis = redis.NewClient(&redis.Options{
	Addr:         ":6379", // TODO: THIS CAN FROM THE ENV or Config
	MinIdleConns: 10,
})

var QueueFactory = redisq.NewFactory()

