package queue

import (
	"context"

	"github.com/redis/go-redis/v9"
	"github.com/vmihailenco/taskq/v3"
	"github.com/vmihailenco/taskq/v3/redisq"
)

var (
	redisClient  *redis.Client
	factory      taskq.Factory
)

// Init initializes the queue factory with a shared Redis v9 client.
func Init(client *redis.Client) {
	redisClient = client
	factory = redisq.NewFactory()
}

// RegisterQueue registers a new queue with the shared redis client.
func RegisterQueue(opts *taskq.QueueOptions) taskq.Queue {
	if opts.Redis == nil {
		opts.Redis = redisClient
	}
	return factory.RegisterQueue(opts)
}

func StartConsumers(ctx context.Context) error {
	return factory.StartConsumers(ctx)
}

func Close() error {
	return factory.Close()
}

// RedisClient returns the shared redis client used by the queue package.
func RedisClient() *redis.Client {
	return redisClient
}

